"""Tests for NetroClient."""

from __future__ import annotations

from typing import Any

import pytest

from pynetro.client import NetroAuthError, NetroClient, NetroConfig, NetroError
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
                "token_reset": "2025-09-29T00:00:00"
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
                        {
                            "name": "Zone 1",
                            "ith": 1,
                            "enabled": True,
                            "smart": "SMART"
                        },
                        {
                            "name": "Zone 2",
                            "ith": 2,
                            "enabled": True,
                            "smart": "SMART"
                        }
                    ]
                }
            }
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
                "token_reset": "2023-04-04T00:00:00"
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
                    "zones": [
                        {
                            "name": "",
                            "ith": 1,
                            "enabled": True,
                            "smart": "ASSISTANT"
                        }
                    ]
                }
            }
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
                "token_reset": "2025-09-29T00:00:00"
            },
            "data": {
                "sensor": {
                    "name": "Example Sensor",
                    "serial": "SSSSSSSSSSSS",
                    "status": "ONLINE",
                    "version": "3.1",
                    "sw_version": "3.1.3",
                    "last_active": "2025-09-28T17:03:26",
                    "battery_level": 0.63
                }
            }
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

    async def test_get_info_api_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with API error response."""
        # Arrange
        test_key = "INVALID_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": "AUTH_001", "message": "invalid key"}],
        }

        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act & Assert
        with pytest.raises(NetroAuthError, match="AUTH_001: invalid key"):
            await client.get_info(test_key)

    async def test_get_info_http_401(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with HTTP 401 error."""
        # Arrange
        test_key = "UNAUTHORIZED_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"

        mock_response = MockHTTPResponse(status=401, should_raise=True)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act & Assert
        with pytest.raises(NetroAuthError):
            await client.get_info(test_key)

    async def test_get_info_generic_api_error(
        self, client: NetroClient, mock_http: MockHTTPClient
    ) -> None:
        """Test get_info with generic API error."""
        # Arrange
        test_key = "ERROR_KEY"
        expected_url = "https://api.netrohome.com/npa/v1/info.json"
        error_response = {
            "status": "ERROR",
            "errors": [{"code": "GEN_001", "message": "Generic error"}],
        }

        mock_response = MockHTTPResponse(status=200, json_data=error_response)
        mock_http.set_response("GET", expected_url, mock_response)

        # Act & Assert
        with pytest.raises(NetroError, match="GEN_001: Generic error"):
            await client.get_info(test_key)

    async def test_get_info_custom_config(self, mock_http: MockHTTPClient) -> None:
        """Test get_info with custom configuration."""
        # Arrange
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

        # Act
        result = await client.get_info(test_key)

        # Assert
        assert result == expected_response
        call = mock_http.get_calls[0]
        assert call["url"] == expected_url
        assert call["kwargs"]["timeout"] == 30.0
        assert call["kwargs"]["headers"]["X-Custom"] == "test"
