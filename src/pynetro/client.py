# src/pynetro/client.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional
import json

from .http import AsyncHTTPClient, AsyncHTTPResponse

# ---------- Exceptions ----------
class NetroError(Exception):
    """Generic Netro client error."""

class NetroAuthError(NetroError):
    """401/403 or API 'ERROR' with auth meaning."""


# ---------- Config ----------
@dataclass(slots=True)
class NetroConfig:
    # Par défaut: base officielle de la NPA v1
    base_url: str = "https://api.netrohome.com/npa/v1"
    default_timeout: float = 10.0
    extra_headers: Optional[Mapping[str, str]] = None


# ---------- Client ----------
class NetroClient:
    """HTTP-agnostic async client for Netro Public API v1."""

    def __init__(self, http: AsyncHTTPClient, config: NetroConfig) -> None:
        base = (config.base_url or "").rstrip("/")
        if not base:
            raise ValueError("NetroConfig.base_url must be provided")
        self._http = http
        self._cfg = config
        self._base = base

    # ---- utils ----
    def _headers_get(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Accept": "application/json"}
        if self._cfg.extra_headers:
            h.update(self._cfg.extra_headers)
        return h

    def _headers_post(self) -> Dict[str, str]:
        h = self._headers_get()
        h.setdefault("Content-Type", "application/json")
        return h

    async def _handle(self, resp: AsyncHTTPResponse) -> Dict[str, Any]:
        """Handle HTTP + NPA JSON envelope."""
        if resp.status in (401, 403):
            try:
                resp.raise_for_status()
            except Exception as e:
                raise NetroAuthError(str(e)) from e
            raise NetroAuthError("Authentication failed")
        resp.raise_for_status()
        data = await resp.json()
        # La NPA renvoie un enveloppe {"status": "OK"/"ERROR", "data": {...}, "meta": {...}}
        status = data.get("status")
        if status and status != "OK":
            # essaie d'extraire un message utile
            errs = data.get("errors") or []
            msg = "; ".join(f"{e.get('code')}: {e.get('message')}" for e in errs if isinstance(errs, list)) or "API ERROR"
            # Certaines erreurs auth ne passent pas par 401/403 → mappe si évident
            if "auth" in msg.lower() or "invalid key" in msg.lower():
                raise NetroAuthError(msg)
            raise NetroError(msg)
        return data  # on retourne l'enveloppe complète (data/meta utiles au caller)

    # ---------- Device APIs ----------
    # GET /npa/v1/info.json?key=ABCDEFG
    async def get_info(self, key: str) -> Dict[str, Any]:
        params = {"key": key}
        url = f"{self._base}/info.json"
        async with self._http.get(url, headers=self._headers_get(), params=params, timeout= self._cfg.default_timeout) as r:
            return await self._handle(r)

    # GET /npa/v1/schedules.json?key=...&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&zones=[1,2]
    async def get_schedules(
        self,
        key: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        zones: Optional[Iterable[int]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if zones is not None:
            # La doc montre zones=[1,2] dans la query → on sérialise en JSON
            params["zones"] = json.dumps(list(zones))
        url = f"{self._base}/schedules.json"
        async with self._http.get(url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # GET /npa/v1/moistures.json?key=...&start_date=&end_date=&zones=[...]
    async def get_moistures(
        self,
        key: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        zones: Optional[Iterable[int]] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if zones is not None:
            params["zones"] = json.dumps(list(zones))
        url = f"{self._base}/moistures.json"
        async with self._http.get(url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # GET /npa/v1/events.json?key=...&event=1&start_date=&end_date=
    async def get_events(
        self,
        key: str,
        *,
        event: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"key": key}
        if event is not None:
            params["event"] = int(event)
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        url = f"{self._base}/events.json"
        async with self._http.get(url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/set_status.json  body={"key": "...", "status": 0/1}
    async def set_status(self, key: str, *, enabled: Optional[bool] = None) -> Dict[str, Any]:
        body: Dict[str, Any] = {"key": key}
        if enabled is not None:
            body["status"] = 1 if enabled else 0
        url = f"{self._base}/set_status.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/water.json body={"key":"...", "zones":[1], "duration": <minutes>, "delay": <minutes>?, "start_time":"YYYY-MM-DD HH:MM"?}
    async def water(
        self,
        key: str,
        *,
        duration_minutes: int,
        zones: Optional[Iterable[int]] = None,
        delay_minutes: Optional[int] = None,
        start_time: Optional[str] = None,  # UTC "YYYY-MM-DD HH:MM" per doc
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"key": key, "duration": int(duration_minutes)}
        if zones is not None:
            body["zones"] = list(zones)
        if delay_minutes is not None:
            body["delay"] = int(delay_minutes)
        if start_time is not None:
            body["start_time"] = start_time
        url = f"{self._base}/water.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/stop_water.json body={"key":"..."}
    async def stop_water(self, key: str) -> Dict[str, Any]:
        body = {"key": key}
        url = f"{self._base}/stop_water.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/no_water.json body={"key":"...", "days": N}
    async def no_water(self, key: str, *, days: int = 1) -> Dict[str, Any]:
        body = {"key": key, "days": int(days)}
        url = f"{self._base}/no_water.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/set_moisture.json body={"key":"...", "zones":[...], "moisture": 0..100}
    async def set_moisture(
        self,
        key: str,
        *,
        moisture: int,
        zones: Optional[Iterable[int]] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"key": key, "moisture": int(moisture)}
        if zones is not None:
            body["zones"] = list(zones)
        url = f"{self._base}/set_moisture.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # POST /npa/v1/report_weather.json body={"key":"...", "date":"YYYY-MM-DD", ...}
    async def report_weather(
        self,
        key: str,
        *,
        date: str,
        condition: Optional[int] = None,
        rain: Optional[float] = None,
        rain_prob: Optional[int] = None,
        temp: Optional[float] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"key": key, "date": date}
        if condition is not None:
            body["condition"] = int(condition)
        if rain is not None:
            body["rain"] = float(rain)
        if rain_prob is not None:
            body["rain_prob"] = int(rain_prob)
        if temp is not None:
            body["temp"] = float(temp)
        url = f"{self._base}/report_weather.json"
        async with self._http.post(url, headers=self._headers_post(), json=body, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)

    # ---------- Sensor APIs ----------
    # GET /npa/v1/sensor_data.json?key=...&start_date=&end_date=
    async def get_sensor_data(
        self,
        key: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"key": key}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        url = f"{self._base}/sensor_data.json"
        async with self._http.get(url, headers=self._headers_get(), params=params, timeout=self._cfg.default_timeout) as r:
            return await self._handle(r)
