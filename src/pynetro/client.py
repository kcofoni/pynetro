"""Async client for Netro Public API v1.

WARNING: Your Netro API key (device serial) gives full access to your devices.
Keep it secret and do not share it.

Provides NetroClient and related classes for interacting with Netro Home's NPA v1 endpoints.
"""

# src/pynetro/client.py
from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from .http import AsyncHTTPClient, AsyncHTTPResponse

# Netro error codes (from official documentation)
NETRO_ERROR_CODE_INVALID_KEY = 1
NETRO_ERROR_CODE_EXCEED_LIMIT = 3
NETRO_ERROR_CODE_INVALID_DEVICE = 4
NETRO_ERROR_CODE_INTERNAL_ERROR = 5
NETRO_ERROR_CODE_PARAMETER_ERROR = 6

def mask(s: str) -> str:
    """Mask a key/serial in logs (keep first 2/last 2 characters)."""
    return re.sub(r"(?<=..).*(?=..)", "****", s) if s and len(s) > 4 else "****"

# ---------- Exceptions ----------
class NetroException(Exception):
    """Netro business error (status == 'ERROR')."""
    def __init__(self, code: int | None, message: str) -> None:
        """Initialize NetroException with error code and message.

        Args:
            code: The error code returned by the API, or None.
            message: The error message describing the issue.
        """
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}" if code is not None else message)

    def __str__(self) -> str:
        """Return a literal error message related to the current exception."""
        return (
            f"A Netro (NPA) error occurred -- error code #{self.code} -> {self.message}"
        )

class NetroInvalidKey(NetroException):
    """Netro error: invalid API key."""

class NetroExceedLimit(NetroException):
    """Netro error: exceed limit."""

class NetroInvalidDevice(NetroException):
    """Netro error: invalid device or sensor."""

class NetroInternalError(NetroException):
    """Netro error: internal error."""

class NetroParameterError(NetroException):
    """Netro error: parameter error."""

# ---------- Config ----------
@dataclass(slots=True)
class NetroConfig:
    """Configuration for NetroClient.

    Attributes:
    ----------
    base_url : str
        Base URL for the Netro Public API v1.
    default_timeout : float
        Default timeout for HTTP requests.
    extra_headers : Optional[Mapping[str, str]]
        Additional headers to include in requests.
    """
    base_url: str = None
    default_timeout: float = 10.0
    extra_headers: Mapping[str, str] | None = None

    # Modifiable class attribute (no type annotation)
    default_base_url = "https://api.netrohome.com/npa/v1"

    def __post_init__(self):
        """Post-initialization hook to set default base_url if not provided."""
        # If base_url is not provided, use the class attribute value
        if self.base_url is None:
            self.base_url = type(self).default_base_url

# ---------- Client ----------
class NetroClient:
    """HTTP-agnostic async client for Netro Public API v1."""

    def __init__(self, http: AsyncHTTPClient, config: NetroConfig) -> None:
        """Initialize NetroClient with an HTTP client and configuration.

        Args:
            http: An asynchronous HTTP client instance.
            config: Configuration settings for the NetroClient.
        """
        base = (config.base_url or "").rstrip("/")
        if not base:
            raise ValueError("NetroConfig.base_url must be provided")
        self._http = http
        self._cfg = config
        self._base = base

    # ---- utils ----
    def _headers_get(self) -> dict[str, str]:
        """Return headers for GET requests."""
        h: dict[str, str] = {"Accept": "application/json"}
        if self._cfg.extra_headers:
            h.update(self._cfg.extra_headers)
        return h

    def _headers_post(self) -> dict[str, str]:
        """Return headers for POST requests."""
        h = self._headers_get()
        h.setdefault("Content-Type", "application/json")
        return h

    async def _handle(self, resp: AsyncHTTPResponse) -> dict[str, Any]:
        """Handle HTTP + NPA JSON envelope."""
        try:
            data = await resp.json()
        except Exception:
            resp.raise_for_status()
            raise

        status = data.get("status")

        if status == "OK":
            return data
        elif status == "ERROR":
            errs = data.get("errors")
            if isinstance(errs, list) and errs:
                err = errs[0]
                code = err.get("code")
                message = err.get("message", "")
                if code == NETRO_ERROR_CODE_INVALID_KEY or "invalid key" in message.lower():
                    raise NetroInvalidKey(code, message)
                if code == NETRO_ERROR_CODE_EXCEED_LIMIT:
                    raise NetroExceedLimit(code, message)
                if code == NETRO_ERROR_CODE_INVALID_DEVICE:
                    raise NetroInvalidDevice(code, message)
                if code == NETRO_ERROR_CODE_INTERNAL_ERROR:
                    raise NetroInternalError(code, message)
                if code == NETRO_ERROR_CODE_PARAMETER_ERROR:
                    raise NetroParameterError(code, message)
                raise NetroException(code, message)
            else:
                raise NetroException(None, "API returned ERROR status without details")
        else:
            resp.raise_for_status()
            msg = f"Unexpected API response status: {status}"
            raise ValueError(msg)

    def get_rate_limit_info(self, response: dict[str, Any]) -> dict[str, Any]:
        """Extract rate limit info from API response."""
        meta = response.get("meta", {})
        return {
            "token_limit": meta.get("token_limit"),
            "token_remaining": meta.get("token_remaining"),
            "token_reset": meta.get("token_reset"),
        }

    def get_transaction_id(self, response: dict[str, Any]) -> str | None:
        """Get transaction ID from API response."""
        return response.get("meta", {}).get("tid")

    def get_api_version(self, response: dict[str, Any]) -> str | None:
        """Get API version from response."""
        return response.get("meta", {}).get("version")

    # ---------- Device APIs ----------
    # GET /npa/v1/info.json?key=ABCDEFG
    async def get_info(self, key: str) -> dict[str, Any]:
        """Retrieve device/account info from the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        params: dict[str, Any] = {"key": key}
        url = f"{self._base}/info.json"
        async with self._http.get(
            url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # GET /npa/v1/schedules.json?key=...&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&zones=[1,2]
    async def get_schedules(
        self,
        key: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        zones: Iterable[int] | None = None,
    ) -> dict[str, Any]:
        """Retrieve watering schedules from the Netro Public API.

        Parameters:
        ----------
        key : str
            API key for authentication.
        start_date : Optional[str], optional
            Start date in "YYYY-MM-DD" format, by default None.
        end_date : Optional[str], optional
            End date in "YYYY-MM-DD" format, by default None.
        zones : Optional[Iterable[int]], optional
            List of zone IDs to filter schedules, by default None.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        params: dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if zones is not None:
            # The docs show zones=[1,2] in query → serialize as JSON
            params["zones"] = json.dumps(list(zones))
        url = f"{self._base}/schedules.json"
        async with self._http.get(
            url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # GET /npa/v1/moistures.json?key=...&start_date=&end_date=&zones=[...]
    async def get_moistures(
        self,
        key: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        zones: Iterable[int] | None = None,
    ) -> dict[str, Any]:
        """Retrieve moisture data from the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        start_date : Optional[str], optional
            Start date in "YYYY-MM-DD" format, by default None.
        end_date : Optional[str], optional
            End date in "YYYY-MM-DD" format, by default None.
        zones : Optional[Iterable[int]], optional
            List of zone IDs to filter moistures, by default None.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        params: dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if zones is not None:
            params["zones"] = json.dumps(list(zones))
        url = f"{self._base}/moistures.json"
        async with self._http.get(
            url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # GET /npa/v1/events.json?key=...&event=1&start_date=&end_date=
    async def get_events(
        self,
        key: str,
        *,
        event: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve event data from the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        event : Optional[int], optional
            Event type to filter, by default None.
        start_date : Optional[str], optional
            Start date in "YYYY-MM-DD" format, by default None.
        end_date : Optional[str], optional
            End date in "YYYY-MM-DD" format, by default None.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        params: dict[str, Any] = {"key": key}
        if event is not None:
            params["event"] = int(event)
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        url = f"{self._base}/events.json"
        async with self._http.get(
            url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/set_status.json  body={"key": "...", "status": 0/1}
    async def set_status(self, key: str, *, enabled: bool | None = None) -> dict[str, Any]:
        """Set the enabled/disabled status of the device via the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        enabled : Optional[bool], optional
            If True, enable the device; if False, disable it; if None, no change.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        body: dict[str, Any] = {"key": key}
        if enabled is not None:
            body["status"] = 1 if enabled else 0
        url = f"{self._base}/set_status.json"
        async with self._http.post(
            url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/water.json body={
    #   "key":"...", "zones":[1], "duration": <minutes>, "delay": <minutes>?,
    #   "start_time":"YYYY-MM-DD HH:MM"?
    # }
    async def water(
        self,
        key: str,
        *,
        duration_minutes: int,
        zones: Iterable[int] | None = None,
        delay_minutes: int | None = None,
        start_time: str | None = None,  # UTC "YYYY-MM-DD HH:MM" per doc
    ) -> dict[str, Any]:
        """Start watering zones via the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        duration_minutes : int
            Duration of watering in minutes.
        zones : Optional[Iterable[int]], optional
            List of zone IDs to water, by default None (all zones).
        delay_minutes : Optional[int], optional
            Delay before starting watering in minutes, by default None.
        start_time : Optional[str], optional
            Scheduled start time in UTC "YYYY-MM-DD HH:MM" format, by default None.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        body: dict[str, Any] = {"key": key, "duration": int(duration_minutes)}
        if zones is not None:
            body["zones"] = list(zones)
        if delay_minutes is not None:
            body["delay"] = int(delay_minutes)
        if start_time is not None:
            body["start_time"] = start_time
        url = f"{self._base}/water.json"
        async with self._http.post(
            url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/stop_water.json body={"key":"..."}
    async def stop_water(self, key: str) -> dict[str, Any]:
        """Stop watering via the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        body = {"key": key}
        url = f"{self._base}/stop_water.json"
        async with self._http.post(
            url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/no_water.json body={"key":"...", "days": N}
    async def no_water(self, key: str, *, days: int = 1) -> dict[str, Any]:
        """Set a no-water period for the device via the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        days : int, optional
            Number of days to prevent watering, by default 1.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        body = {"key": key, "days": int(days)}
        url = f"{self._base}/no_water.json"
        async with self._http.post(
            url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/set_moisture.json body={"key":"...", "zones":[...], "moisture": 0..100}
    async def set_moisture(
        self,
        key: str,
        *,
        moisture: int,
        zones: Iterable[int] | None = None,
    ) -> dict[str, Any]:
        """Set the moisture level for specified zones via the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        moisture : int
            Moisture value to set (0..100).
        zones : Optional[Iterable[int]], optional
            List of zone IDs to set moisture for, by default None (all zones).

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        body: dict[str, Any] = {"key": key, "moisture": int(moisture)}
        if zones is not None:
            body["zones"] = list(zones)
        url = f"{self._base}/set_moisture.json"
        async with self._http.post(
            url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)

    # POST /npa/v1/report_weather.json body={"key":"...", "date":"YYYY-MM-DD", ...}
    async def report_weather(
        self,
        key: str,
        *,
        date: str,
        condition: int | None = None,   # 0: clear, 1: cloudy, 2: rain, 3: snow, 4: wind
        rain: float | None = None,      # mm
        rain_prob: int | None = None,   # [0,100]
        temp: float | None = None,      # °C (average)
        t_min: float | None = None,     # °C
        t_max: float | None = None,     # °C
        t_dew: float | None = None,     # °C (dew point)
        wind_speed: float | None = None,# m/s
        humidity: int | None = None,    # [0,100]
        pressure: float | None = None,  # hPa
    ) -> dict[str, Any]:
        """POST /npa/v1/report_weather.json — override system weather."""
        body: dict[str, Any] = {"key": key, "date": date}

        if condition is not None:
            if condition not in (0, 1, 2, 3, 4):
                raise ValueError("condition must be one of {0,1,2,3,4}")
            body["condition"] = int(condition)

        if rain is not None:
            body["rain"] = float(rain)

        if rain_prob is not None:
            rp = int(rain_prob)
            if not 0 <= rp <= 100:
                raise ValueError("rain_prob must be in [0, 100]")
            body["rain_prob"] = rp

        if temp is not None:
            body["temp"] = float(temp)
        if t_min is not None:
            body["t_min"] = float(t_min)
        if t_max is not None:
            body["t_max"] = float(t_max)
        if t_dew is not None:
            body["t_dew"] = float(t_dew)
        if wind_speed is not None:
            body["wind_speed"] = float(wind_speed)

        if humidity is not None:
            h = int(humidity)
            if not 0 <= h <= 100:
                raise ValueError("humidity must be in [0, 100]")
            body["humidity"] = h

        if pressure is not None:
            body["pressure"] = float(pressure)

        url = f"{self._base}/report_weather.json"
        async with self._http.post(
            url,
            headers=self._headers_post(),
            json=body,
            timeout=self._cfg.default_timeout,
        ) as r:
            return await self._handle(r)

    # ---------- Sensor APIs ----------
    # GET /npa/v1/sensor_data.json?key=...&start_date=&end_date=
    async def get_sensor_data(
        self,
        key: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve sensor data from the Netro Public API.

        Parameters
        ----------
        key : str
            API key for authentication.
        start_date : Optional[str], optional
            Start date in "YYYY-MM-DD" format, by default None.
        end_date : Optional[str], optional
            End date in "YYYY-MM-DD" format, by default None.

        Returns:
        -------
        dict[str, Any]
            The full JSON envelope returned by the API.
        """
        params: dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        url = f"{self._base}/sensor_data.json"
        async with self._http.get(
            url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout
        ) as r:
            return await self._handle(r)
