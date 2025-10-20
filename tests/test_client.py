"""Tests for NetroClient."""  # pylint: disable=C0302

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pynetro.client import (
    NETRO_ERROR_CODE_EXCEED_LIMIT,
    NETRO_ERROR_CODE_INVALID_KEY,
    NetroClient,
    NetroConfig,
    NetroExceedLimit,
    NetroException,
    NetroInternalError,
    NetroInvalidDevice,
    NetroInvalidKey,
    NetroParameterError,
    mask,
)
from pynetro.http import AsyncHTTPResponse


class MockHTTPResponse:
    """Mock HTTP response that implements AsyncHTTPResponse protocol."""

    def __init__(
        self,
        status: int = 200,
        json_data: dict[str, Any] | None = None,
        text_data: str = "",
        should_raise: bool = False,
    ) -> None:
        """Initialize mock response.

        Args:
            status: HTTP status code
            json_data: JSON data to return from json() method
            text_data: Text data to return from text() method
            should_raise: Whether raise_for_status() should raise an exception
        """
        self.status = status
        self._json_data = json_data or {}
        self._text_data = text_data
        self._should_raise = should_raise

    async def json(self) -> Any:
        """Return mock JSON data."""
        return self._json_data

    async def text(self) -> str:
        """Return mock text data."""
        return self._text_data

    def raise_for_status(self) -> None:
        """Raise exception if configured to do so."""
        if self._should_raise:
            msg = f"HTTP {self.status} error"
            raise RuntimeError(msg)

    async def __aenter__(self) -> MockHTTPResponse:
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Context manager exit."""


class MockHTTPClient:
    """Mock HTTP client that implements AsyncHTTPClient protocol."""

    def __init__(self) -> None:
        """Initialize mock client with tracking for calls."""
        self.get_calls: list[dict[str, Any]] = []
        self.post_calls: list[dict[str, Any]] = []
        self.put_calls: list[dict[str, Any]] = []
        self.delete_calls: list[dict[str, Any]] = []
        self._responses: dict[str, MockHTTPResponse] = {}

    def set_response(self, method: str, url: str, response: MockHTTPResponse) -> None:
        """Configure mock response for a specific method/URL."""
        key = f"{method.upper()}:{url}"
        self._responses[key] = response

    def _get_response(self, method: str, url: str) -> MockHTTPResponse:
        """Get configured response or default."""
        key = f"{method.upper()}:{url}"
        return self._responses.get(key, MockHTTPResponse())

    def get(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Mock GET request."""
        self.get_calls.append({"url": url, "kwargs": kwargs})
        return self._get_response("GET", url)

    def post(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Mock POST request."""
        self.post_calls.append({"url": url, "kwargs": kwargs})
        return self._get_response("POST", url)

    def put(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Mock PUT request."""
        self.put_calls.append({"url": url, "kwargs": kwargs})
        return self._get_response("PUT", url)

    def delete(self, url: str, **kwargs) -> AsyncHTTPResponse:
        """Mock DELETE request."""
        self.delete_calls.append({"url": url, "kwargs": kwargs})
        return self._get_response("DELETE", url)


class TestNetroClient:
    """Test cases for NetroClient."""

    @pytest.fixture
    def mock_http(self) -> MockHTTPClient:
        """Provide a mock HTTP client."""
        return MockHTTPClient()

    @pytest.fixture
    def config(self) -> NetroConfig:
        """Provide default configuration."""
        return NetroConfig()

    @pytest.fixture
    def client(self, mock_http: MockHTTPClient, config: NetroConfig) -> NetroClient:
        """Provide a NetroClient with mock HTTP client."""
        return NetroClient(mock_http, config)

    async def test_get_sprite_info_success(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test successful get_info call for Sprite controller (AC-powered, multi-zone)."""
        # Arrange
        test_key = "YYYYYYYYYYYY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        expected_response = {
            "status": "OK",
            "meta": {
                "time": "2025-09-28T20:14:48",
                "tid": "1759090488_MfGR",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 704,
                "last_active": "2025-09-28T20:14:48",
                "token_reset": "2025-09-29T00:00:00",
            },
            "data": {
                "device": {
                    "name": "Example Controller",
                    "serial": "YYYYYYYYYYYY",
                    "status": "ONLINE",
                    "version": "1.2",
                    "sw_version": "1.1.1",
                    "last_active": "2025-09-28T17:28:58",
                    "zone_num": 6,
                    "zones": [
                        {"name": "Zone 1", "ith": 1, "enabled": True, "smart": "SMART"},
                        {"name": "Zone 2", "ith": 2, "enabled": True, "smart": "SMART"},
                    ],
                }
            },
        }

        # Configure mock response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act
        result = await client.get_info(test_key)

        # Assert
        assert result == expected_response
        assert len(mock_http.get_calls) == 1

        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["params"] == {"key": test_key}
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"]["Accept"] == "application/json"
        assert call["kwargs"]["timeout"] == 10.0

        # Verify Sprite-specific data structure
        device_data = result["data"]["device"]
        assert device_data["serial"] == test_key
        assert "zone_num" in device_data
        assert device_data["zone_num"] > 1  # Multi-zone
        assert "zones" in device_data
        assert len(device_data["zones"]) > 1
        assert "battery_level" not in device_data  # AC-powered, no battery

    async def test_get_pixie_info_success(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test successful get_info call for Pixie controller (battery-powered, single-zone)."""
        # Arrange
        test_key = "XXXXXXXX"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        expected_response = {
            "status": "OK",
            "meta": {
                "time": "2023-04-03T14:30:49",
                "tid": "1680532249_LbYQ",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 1999,
                "last_active": "2023-04-03T14:30:49",
                "token_reset": "2023-04-04T00:00:00",
            },
            "data": {
                "device": {
                    "name": "Pixie",
                    "serial": "XXXXXXXX",
                    "zone_num": 1,
                    "status": "ONLINE",
                    "version": "1.3",
                    "sw_version": "1.3.2",
                    "last_active": "2023-04-03T14:26:06",
                    "battery_level": 0.81,
                    "zones": [{"name": "", "ith": 1, "enabled": True, "smart": "ASSISTANT"}],
                }
            },
        }

        # Configure mock response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act
        result = await client.get_info(test_key)

        # Assert
        assert result == expected_response
        assert len(mock_http.get_calls) == 1

        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["params"] == {"key": test_key}
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"]["Accept"] == "application/json"
        assert call["kwargs"]["timeout"] == 10.0

        # Verify Pixie-specific data structure
        device_data = result["data"]["device"]
        assert device_data["serial"] == test_key
        assert "zone_num" in device_data
        assert device_data["zone_num"] == 1  # Single-zone
        assert "zones" in device_data
        assert len(device_data["zones"]) == 1
        assert "battery_level" in device_data  # Battery-powered
        assert isinstance(device_data["battery_level"], float)
        assert 0.0 <= device_data["battery_level"] <= 1.0

    async def test_get_sens_info_success(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test successful get_info call for sensor device."""
        # Arrange
        test_key = "SSSSSSSSSSSS"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        expected_response = {
            "status": "OK",
            "meta": {
                "time": "2025-09-28T20:14:48",
                "tid": "1759090488_MfGR",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 704,
                "last_active": "2025-09-28T20:14:48",
                "token_reset": "2025-09-29T00:00:00",
            },
            "data": {
                "sensor": {
                    "name": "Example Sensor",
                    "serial": "SSSSSSSSSSSS",
                    "status": "ONLINE",
                    "version": "3.1",
                    "sw_version": "3.1.3",
                    "last_active": "2025-09-28T17:03:26",
                    "battery_level": 0.63,
                }
            },
        }

        # Configure mock response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act
        result = await client.get_info(test_key)

        # Assert
        assert result == expected_response
        assert len(mock_http.get_calls) == 1

        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["params"] == {"key": test_key}
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"]["Accept"] == "application/json"
        assert call["kwargs"]["timeout"] == 10.0

        # Verify sensor-specific data structure
        sensor_data = result["data"]["sensor"]
        assert sensor_data["serial"] == test_key
        assert "battery_level" in sensor_data
        assert isinstance(sensor_data["battery_level"], float)
        assert 0.0 <= sensor_data["battery_level"] <= 1.0

    async def test_get_info_api_error(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """Test get_info with API error response (invalid key)."""
        test_key = "INVALID_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": NETRO_ERROR_CODE_INVALID_KEY, "message": "Invalid key: test"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(NetroInvalidKey) as exc_info:
            await client.get_info(test_key)
        assert exc_info.value.code == NETRO_ERROR_CODE_INVALID_KEY
        assert "Invalid key" in exc_info.value.message
        assert str(exc_info.value).startswith("A Netro (NPA) error occurred")

    async def test_get_info_exceed_limit_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with API error response (exceed limit)."""
        test_key = "ERROR_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": NETRO_ERROR_CODE_EXCEED_LIMIT, "message": "Exceed limit"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(NetroExceedLimit) as exc_info:
            await client.get_info(test_key)
        assert exc_info.value.code == NETRO_ERROR_CODE_EXCEED_LIMIT
        assert "Exceed limit" in exc_info.value.message

    async def test_get_info_http_401(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """Test get_info with HTTP 401 error."""
        test_key = "UNAUTHORIZED_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        mock_response = MockHTTPResponse(status=401, should_raise=True)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(RuntimeError):
            await client.get_info(test_key)

    async def test_get_info_invalid_device_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with API error response (invalid device or sensor)."""
        test_key = "ERROR_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": 4, "message": "Invalid device or sensor"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(NetroInvalidDevice) as exc_info:
            await client.get_info(test_key)
        assert exc_info.value.code == 4
        assert "Invalid device" in exc_info.value.message or "sensor" in exc_info.value.message

    async def test_get_info_internal_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with API error response (internal error)."""
        test_key = "ERROR_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": 5, "message": "Internal error"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(NetroInternalError) as exc_info:
            await client.get_info(test_key)
        assert exc_info.value.code == 5
        assert "Internal error" in exc_info.value.message

    async def test_get_info_parameter_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with API error response (parameter error)."""
        test_key = "ERROR_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": 6, "message": "Parameter error"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        with pytest.raises(NetroParameterError) as exc_info:
            await client.get_info(test_key)
        assert exc_info.value.code == 6
        assert "Parameter error" in exc_info.value.message

    async def test_get_info_custom_config(self, mock_http: MockHTTPClient) -> None:
        """Test get_info with custom configuration."""
        custom_config = NetroConfig(
            base_url="https://custom.api.com/v2",
            default_timeout=30.0,
            extra_headers={"X-Custom": "test"},
        )
        client = NetroClient(mock_http, custom_config)

        test_key = "CUSTOM_KEY"
        expected_url = "https://custom.api.com/v2/info.json"
        expected_response = {"status": "OK", "data": {}}

        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        result = await client.get_info(test_key)
        assert result == expected_response
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["timeout"] == 30.0
        assert call["kwargs"]["headers"]["X-Custom"] == "test"

    async def test_handle_invalid_key_error(
        self,
        client: NetroClient,
    ) -> None:
        """Test _handle for invalid key error."""
        response_data = {
            "status": "ERROR",
            "errors": [{"code": NETRO_ERROR_CODE_INVALID_KEY, "message": "Invalid key: test"}],
        }
        mock_response = MockHTTPResponse(status=200, json_data=response_data)
        with pytest.raises(NetroInvalidKey) as exc_info:
            await client._handle(mock_response) # pylint: disable=W0212
        assert exc_info.value.code == NETRO_ERROR_CODE_INVALID_KEY
        assert isinstance(exc_info.value.code, int)
        assert "Invalid key" in exc_info.value.message
        assert str(exc_info.value).startswith("A Netro (NPA) error occurred")

    async def test_handle_other_business_error(
        self, client: NetroClient
    ) -> None:
        """Test _handle for other business error."""
        response_data = {"status": "ERROR", "errors": [{"code": 3, "message": "Exceed limit"}]}
        mock_response = MockHTTPResponse(status=200, json_data=response_data)
        with pytest.raises(NetroException) as exc_info:
            await client._handle(mock_response) # pylint: disable=W0212
        assert exc_info.value.code == 3
        assert isinstance(exc_info.value.code, int)
        assert "Exceed limit" in exc_info.value.message

    async def test_get_schedules_controller_success(
        self, client: NetroClient, mock_http: MockHTTPClient, need_schedules_reference  # pylint: disable=W0613
    ) -> None:
        """Test get_schedules for a controller with date range and zones using reference JSON."""
        test_key = "TESTKEY123"
        expected_url = "https://api.netrohome.com/npa/v1/schedules.json"

        # provide start/end dates and zones
        start_date = "2025-09-29"
        end_date = "2025-10-25"
        zones = [1, 2, 3]

        # Load reference response from tests/reference_data
        ref_file = Path(__file__).parent / "reference_data" / "sprite_response_schedules.json"
        if not ref_file.exists():
            pytest.skip(f"Reference file missing: {ref_file}")
        with ref_file.open(encoding="utf-8") as fh:
            expected_response = json.load(fh)

        # Configure mock response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act
        result = await client.get_schedules(test_key, start_date=start_date, end_date=end_date, zones=zones)

        # Assert - response equality and request parameters
        assert result == expected_response
        assert len(mock_http.get_calls) == 1
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url

        expected_params = {
            "key": test_key,
            "start_date": start_date,
            "end_date": end_date,
            "zones": json.dumps(list(zones)),
        }
        assert call["kwargs"]["params"] == expected_params
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"]["Accept"] == "application/json"

        # Validate returned schedules structure (basic checks)
        assert "data" in result
        data = result["data"]
        assert isinstance(data, dict)
        assert "schedules" in data or any("schedule" in k for k in data.keys())
        schedules = data.get("schedules", next((v for k, v in data.items() if "schedule" in k), []))
        assert isinstance(schedules, list)
        if schedules:
            sample = schedules[0]
            assert isinstance(sample, dict)
            assert "zone" in sample or "id" in sample
            assert any(k in sample for k in ("start_time", "local_start_time", "time"))

    async def test_get_moistures_controller_success(
        self, client: NetroClient, mock_http: MockHTTPClient, need_moistures_reference  # pylint: disable=W0613
    ) -> None:
        """Test get_moistures for a controller with date range and zones using reference JSON."""
        test_key = "TESTKEY123"
        expected_url = "https://api.netrohome.com/npa/v1/moistures.json"

        # provide start/end dates and zones
        start_date = "2025-09-29"
        end_date = "2025-10-25"
        zones = [1, 2, 3]

        # Load reference response from tests/reference_data
        ref_file = Path(__file__).parent / "reference_data" / "sprite_response_moistures.json"
        if not ref_file.exists():
            pytest.skip(f"Reference file missing: {ref_file}")
        with ref_file.open(encoding="utf-8") as fh:
            expected_response = json.load(fh)

        # Configure mock response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act
        result = await client.get_moistures(test_key, start_date=start_date, end_date=end_date, zones=zones)

        # Assert - response equality and request parameters
        assert result == expected_response
        assert len(mock_http.get_calls) == 1
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url

        expected_params = {
            "key": test_key,
            "start_date": start_date,
            "end_date": end_date,
            "zones": json.dumps(list(zones)),
        }
        assert call["kwargs"]["params"] == expected_params
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"]["Accept"] == "application/json"

        # Validate returned moistures structure (basic checks)
        assert "data" in result
        data = result["data"]
        assert isinstance(data, dict)
        moisture_key = "moistures" if "moistures" in data else next((k for k in data.keys() if "moist" in k), None)
        assert moisture_key is not None, "Response should contain a moisture list (e.g. 'moistures')"

        moistures = data.get(moisture_key, [])
        assert isinstance(moistures, list)
        if moistures:
            sample = moistures[0]
            assert isinstance(sample, dict)
            # common expected fields in a moisture entry
            assert "zone" in sample or "id" in sample
            assert any(k in sample for k in ("moisture", "value", "time"))

    async def test_get_events_with_filters(
        self,
        client: NetroClient,
        mock_http: MockHTTPClient,
        need_events_reference,  # ensure reference file exists (copied from template if needed)  # pylint: disable=W0613
    ) -> None:
        """GET events with event type and date range — use reference sprite_response_events.json."""
        test_key = "TESTKEY-EVENTS"
        expected_url = f"{client._base}/events.json"  # pylint: disable=W0212

        # Load reference response
        ref_file = Path(__file__).parent / "reference_data" / "sprite_response_events.json"
        if not ref_file.exists():
            pytest.skip(f"Reference file missing: {ref_file}")
        with ref_file.open(encoding="utf-8") as fh:
            expected_response = json.load(fh)

        # Configure mock HTTP to return the reference
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Call with filters
        event_type = 3
        start_date = "2025-09-01"
        end_date = "2025-10-31"
        result = await client.get_events(test_key, event=event_type, start_date=start_date, end_date=end_date)

        # Basic assertions
        assert result == expected_response
        assert getattr(mock_http, "get_calls", None) and len(mock_http.get_calls) == 1
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url

        expected_params = {"key": test_key, "event": int(event_type), "start_date": start_date, "end_date": end_date}
        assert call["kwargs"]["params"] == expected_params
        assert "headers" in call["kwargs"] and call["kwargs"]["headers"].get("Accept") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

        # Verify events present in response
        data = result.get("data", {})
        events = data.get("events")
        assert isinstance(events, list) and len(events) > 0, "expected at least one event in response"
        # verify minimal shape for first item
        first = events[0]
        assert "id" in first and "event" in first and "time" in first and "message" in first

    def test_mask_long_string(self):
        """Ensure mask preserves the first two and last two characters for strings longer than four."""
        assert mask("ABCDEFGH") == "AB****GH"
        assert mask("12345678") == "12****78"
        # preserves first 2 and last 2 chars for strings longer than 4

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("abcd", "****"),   # length == 4 -> masked
            ("abc", "****"),    # length < 4 -> masked
            ("", "****"),       # empty -> masked
            (None, "****"),     # None -> masked (function treats falsy as masked)
        ],
    )
    def test_mask_short_or_empty(self, value, expected):
        """Test mask() behavior for short, empty or None inputs (should return '****')."""
        assert mask(value) == expected

    async def test_set_status_enable(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST set_status -> enabled True should send status=1 and return parsed response."""
        test_key = "TESTKEY-SET-1"
        expected_url = f"{client._base}/set_status.json"  # pylint: disable=W0212

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.set_status(test_key, enabled=True)

        assert result == expected_response

        # Basic response structure assertions (meta and data shape)
        assert isinstance(result, dict)
        assert result.get("status") == "OK"
        assert "meta" in result and isinstance(result["meta"], dict)
        assert "data" in result and isinstance(result["data"], dict)

        # ensure one POST call was made
        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1, "expected one POST call"
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "status": 1}
        assert "headers" in call["kwargs"]
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_set_status_disable(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST set_status -> enabled False should send status=0."""
        test_key = "TESTKEY-SET-0"
        expected_url = f"{client._base}/set_status.json"  # pylint: disable=W0212

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.set_status(test_key, enabled=False)

        assert result == expected_response

        # Basic response structure assertions
        assert isinstance(result, dict)
        assert result.get("status") == "OK"
        assert "meta" in result and isinstance(result["meta"], dict)
        assert "data" in result and isinstance(result["data"], dict)

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "status": 0}

    async def test_set_status_no_change(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST set_status with enabled=None should send only the key (no status field)."""
        test_key = "TESTKEY-SET-NONE"
        expected_url = f"{client._base}/set_status.json"  # pylint: disable=W0212

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.set_status(test_key, enabled=None)

        assert result == expected_response

        # Basic response structure assertions
        assert isinstance(result, dict)
        assert result.get("status") == "OK"
        assert "meta" in result and isinstance(result["meta"], dict)
        assert "data" in result and isinstance(result["data"], dict)

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key}

    async def test_no_water_default_days(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST no_water -> default days (1) should be sent and response parsed."""
        test_key = "TESTKEY-NO-WATER-DEF"
        expected_url = f"{client._base}/no_water.json"  # pylint: disable=W0212

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.no_water(test_key)

        assert result == expected_response
        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "days": 1}
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_no_water_custom_days(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST no_water -> custom days should be coerced to int and sent."""
        test_key = "TESTKEY-NO-WATER-3"
        expected_url = f"{client._base}/no_water.json"  # pylint: disable=W0212
        days = 3

        expected_response = {"status": "OK", "meta": {}, "data": {}}

        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.no_water(test_key, days=days)

        assert result == expected_response
        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "days": int(days)}
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_report_weather_all_params(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """POST report_weather with all optional parameters set."""
        test_key = "TESTKEY-REPORT"
        expected_url = f"{client._base}/report_weather.json"  # pylint: disable=W0212

        date = "2025-10-20"
        params = {
            "condition": 2,
            "rain": 12.5,
            "rain_prob": 80,
            "temp": 15.3,
            "t_min": 10.0,
            "t_max": 20.0,
            "t_dew": 8.5,
            "wind_speed": 3.2,
            "humidity": 60,
            "pressure": 1013.2,
        }

        expected_body = {
            "key": test_key,
            "date": date,
            "condition": int(params["condition"]),
            "rain": float(params["rain"]),
            "rain_prob": int(params["rain_prob"]),
            "temp": float(params["temp"]),
            "t_min": float(params["t_min"]),
            "t_max": float(params["t_max"]),
            "t_dew": float(params["t_dew"]),
            "wind_speed": float(params["wind_speed"]),
            "humidity": int(params["humidity"]),
            "pressure": float(params["pressure"]),
        }

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        # Act
        result = await client.report_weather(
            test_key,
            date=date,
            condition=params["condition"],
            rain=params["rain"],
            rain_prob=params["rain_prob"],
            temp=params["temp"],
            t_min=params["t_min"],
            t_max=params["t_max"],
            t_dew=params["t_dew"],
            wind_speed=params["wind_speed"],
            humidity=params["humidity"],
            pressure=params["pressure"],
        )

        # Assert
        assert result == expected_response

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == expected_body
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_report_weather_invalid_condition(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """report_weather should raise ValueError for invalid condition values."""
        test_key = "TESTKEY-REPORT-INVALID"
        # invalid condition (not in 0..4)
        with pytest.raises(ValueError) as excinfo:
            await client.report_weather(test_key, date="2025-10-20", condition=9)
        # Assert on exception message content (be permissive / use substring)
        msg = str(excinfo.value)
        assert "condition" in msg and ("0" in msg or "0..4" in msg or "one of" in msg)

        # ensure no HTTP request was sent
        assert not getattr(mock_http, "post_calls", None)

    async def test_report_weather_invalid_rain_prob(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """report_weather should raise ValueError when rain_prob is outside [0,100]."""
        test_key = "TESTKEY-REPORT-INVALID-RP"
        # too large
        with pytest.raises(ValueError) as excinfo1:
            await client.report_weather(test_key, date="2025-10-20", rain_prob=150)
        assert "rain_prob" in str(excinfo1.value) and "0" in str(excinfo1.value)

        # too small
        with pytest.raises(ValueError) as excinfo2:
            await client.report_weather(test_key, date="2025-10-20", rain_prob=-1)
        assert "rain_prob" in str(excinfo2.value) and "0" in str(excinfo2.value)

        # ensure no HTTP request was sent
        assert not getattr(mock_http, "post_calls", None)

    async def test_get_sensor_data(
        self,
        client: NetroClient,
        mock_http: MockHTTPClient,
        need_sensor_data_reference,  # assure la présence (copie du template si nécessaire)  : pylint: disable=W0613
    ) -> None:
        """GET get_sensor_data using tests/reference_data/sensor_response_data.json."""
        test_key = "TESTKEY-SENSOR-REF"
        expected_url = f"{client._base}/sensor_data.json"  # pylint: disable=W0212

        # Load reference response (fixture ensure_reference gère l'existence)
        ref_file = Path(__file__).parent / "reference_data" / "sensor_response_data.json"
        if not ref_file.exists():
            pytest.skip(f"Reference file missing: {ref_file}")
        with ref_file.open(encoding="utf-8") as fh:
            expected_response = json.load(fh)

        # Configure mock HTTP to return the reference response
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act - call with a date range
        start_date = "2025-10-10"
        end_date = "2025-10-12"
        result = await client.get_sensor_data(test_key, start_date=start_date, end_date=end_date)

        # Assert - response and request correctness
        assert result == expected_response
        assert getattr(mock_http, "get_calls", None) and len(mock_http.get_calls) == 1
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["params"] == {"key": test_key, "start_date": start_date, "end_date": end_date}
        assert "headers" in call["kwargs"] and call["kwargs"]["headers"]["Accept"] == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_set_moisture_with_zones(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST set_moisture -> send moisture percent and zones, parse response."""
        test_key = "TESTKEY-MOISTURE"
        expected_url = f"{client._base}/set_moisture.json"  # pylint: disable=W0212

        # use an example moisture % and multiple zones
        moisture = 45
        zones = [1, 2]

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        # Act
        result = await client.set_moisture(test_key, moisture=moisture, zones=zones)

        # Assert
        assert result == expected_response

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "moisture": int(moisture), "zones": list(zones)}
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    async def test_water_with_delay_and_zones(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST water with duration, delay and zones should send correct body and return schedules."""
        test_key = "TESTKEY-WATER-1"
        expected_url = f"{client._base}/water.json"  # pylint: disable=W0212

        duration = 10
        delay = 60
        zones = [1]

        expected_response = {
            "status": "OK",
            "meta": {
                "token_reset": "2025-10-20T00:00:00",
                "time": "2025-10-19T22:43:23",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 319,
                "tid": "1760913803_kHUP",
                "last_active": "2025-10-19T22:43:23",
            },
            "data": {
                "schedules": [
                    {
                        "zone": 1,
                        "end_time": "2025-10-19T23:53:23",
                        "local_end_time": "01:53:23",
                        "id": 486321588,
                        "source": "MANUAL",
                        "start_time": "2025-10-19T23:43:23",
                        "local_date": "2025-10-20",
                        "status": "VALID",
                        "local_start_time": "01:43:23",
                    }
                ]
            },
        }

        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.water(test_key, duration_minutes=duration, zones=zones, delay_minutes=delay)

        assert result == expected_response

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "duration": int(duration), "zones": list(zones), "delay": int(delay)}
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

        # Verify schedules present
        data = result.get("data", {})
        sched_key = "schedules" if "schedules" in data else next((k for k in data.keys() if "schedule" in k), None)
        assert sched_key is not None, "Response should contain schedules"
        schedules = data[sched_key]
        assert isinstance(schedules, list) and len(schedules) > 0

    async def test_water_with_start_time_and_zones(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST water with explicit start_time and zones should send start_time and return schedules."""
        test_key = "TESTKEY-WATER-2"
        expected_url = f"{client._base}/water.json"  # pylint: disable=W0212

        duration = 12
        start_time = "2025-10-25 08:00"
        zones = [1]

        expected_response = {
            "status": "OK",
            "meta": {
                "token_reset": "2025-10-20T00:00:00",
                "time": "2025-10-19T22:42:55",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 320,
                "tid": "1760913775_IHhB",
                "last_active": "2025-10-19T22:42:55",
            },
            "data": {
                "schedules": [
                    {
                        "zone": 1,
                        "end_time": "2025-10-25T08:12:00",
                        "local_end_time": "10:12:00",
                        "id": 486321577,
                        "source": "MANUAL",
                        "start_time": "2025-10-25T08:00:00",
                        "local_date": "2025-10-25",
                        "status": "VALID",
                        "local_start_time": "10:00:00",
                    }
                ]
            },
        }

        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        result = await client.water(test_key, duration_minutes=duration, zones=zones, start_time=start_time)

        assert result == expected_response

        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key, "duration": int(duration), "zones": list(zones), "start_time": start_time}
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

        # Verify schedules present
        data = result.get("data", {})
        sched_key = "schedules" if "schedules" in data else next((k for k in data.keys() if "schedule" in k), None)
        assert sched_key is not None, "Response should contain schedules"
        schedules = data[sched_key]
        assert isinstance(schedules, list) and len(schedules) > 0

    async def test_stop_water(self, client: NetroClient, mock_http: MockHTTPClient) -> None:
        """POST stop_water should send the key and return parsed response."""
        test_key = "TESTKEY-STOP"
        expected_url = f"{client._base}/stop_water.json"  # pylint: disable=W0212

        expected_response = {"status": "OK", "meta": {}, "data": {}}
        mock_response = MockHTTPResponse(status=200, json_data=expected_response)
        mock_http.set_response("POST", expected_url, mock_response)

        # Act
        result = await client.stop_water(test_key)

        # Assert
        assert result == expected_response
        post_calls = getattr(mock_http, "post_calls", None)
        assert post_calls and len(post_calls) == 1
        call = post_calls[0]

        assert call["url"] == expected_url
        assert call["kwargs"]["json"] == {"key": test_key}
        assert call["kwargs"]["headers"].get("Content-Type") == "application/json"
        assert call["kwargs"]["timeout"] == client._cfg.default_timeout  # pylint: disable=W0212

    def test_meta_helpers_from_response(self, client: NetroClient) -> None:
        """Extract rate-limit info, transaction id and API version from response meta."""
        response = {
            "status": "OK",
            "meta": {
                "token_reset": "2025-10-20T00:00:00",
                "time": "2025-10-19T22:42:55",
                "version": "1.0",
                "token_limit": 2000,
                "token_remaining": 320,
                "tid": "1760913775_IHhB",
                "last_active": "2025-10-19T22:42:55",
            },
            "data": {},
        }

        rate = client.get_rate_limit_info(response)
        assert rate == {
            "token_limit": 2000,
            "token_remaining": 320,
            "token_reset": "2025-10-20T00:00:00",
        }

        assert client.get_transaction_id(response) == "1760913775_IHhB"
        assert client.get_api_version(response) == "1.0"
