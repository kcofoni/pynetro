"""Integration tests for NetroClient with real HTTP client.

These tests require a real Netro API key and internet connection.
They are marked as 'integration' to run them separately.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pynetro.client import (
    NetroClient,
    NetroConfig,
    NetroInvalidKey,
)

from .aiohttp_client import AiohttpClient

# Environment variables for integration tests
NETRO_API_KEY = os.environ.get("NETRO_API_KEY")
NETRO_CTRL_SERIAL = os.environ.get("NETRO_CTRL_SERIAL")
NETRO_SENS_SERIAL = os.environ.get("NETRO_SENS_SERIAL")

# Skip integration tests if required environment variables are not provided
skip_if_no_key = pytest.mark.skipif(
    not NETRO_API_KEY, reason="NETRO_API_KEY environment variable not set"
)

skip_if_no_serials = pytest.mark.skipif(
    not (NETRO_CTRL_SERIAL and NETRO_SENS_SERIAL),
    reason="NETRO_CTRL_SERIAL and/or NETRO_SENS_SERIAL environment variables not set",
)


@pytest.mark.integration
class TestNetroClientIntegration:
    """Integration tests with real Netro API."""

    @pytest.fixture
    async def real_http_client(self) -> AsyncIterator[AiohttpClient]:
        """Provide a real HTTP client."""
        async with AiohttpClient() as client:
            yield client

    @pytest.fixture
    def config(self) -> NetroConfig:
        """Provide default configuration for real API."""
        return NetroConfig()

    @pytest.fixture
    async def client(self, real_http_client: AiohttpClient, config: NetroConfig) -> NetroClient:
        """Provide a NetroClient with real HTTP client."""
        return NetroClient(real_http_client, config)

    @skip_if_no_serials
    async def test_get_info_sensor_device(self, client: NetroClient, need_sensor_reference) -> None:  #pylint: disable=W0613
        """Test get_info with Netro sensor device and validate against reference structure."""
        # Arrange - Sensor serial from environment
        sensor_key = NETRO_SENS_SERIAL
        if sensor_key is None:
            pytest.skip("NETRO_SENS_SERIAL environment variable not set")

        # Load reference structure (must exist for this integration test)
        reference_file = Path(__file__).parent / "reference_data" / "sensor_response.json"
        if not reference_file.exists():
            pytest.skip(f"Reference file missing: {reference_file}")
        with reference_file.open() as f:
            reference_data = json.load(f)

        # Act
        result = await client.get_info(sensor_key)

        # Assert - Verify sensor response structure
        assert isinstance(result, dict)
        assert result["status"] == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        assert "sensor" in data, "Response should contain 'sensor' for sensor device"

        sensor_info = data["sensor"]
        assert sensor_info["serial"] == sensor_key
        assert "name" in sensor_info
        assert "status" in sensor_info
        assert "battery_level" in sensor_info

        # Validate against reference structure if available
        if reference_data:
            print("🔍 Validating sensor against reference structure...")
            reference_sensor = reference_data["data"]["sensor"]

            # Check that all expected fields from reference are present
            for field in reference_sensor.keys():
                assert field in sensor_info, f"Missing expected field: {field}"

            # Validate sensor-specific fields
            assert sensor_info["serial"] == reference_sensor["serial"]
            battery_level = sensor_info["battery_level"]
            assert isinstance(battery_level, (int, float)), "battery_level should be numeric"
            assert 0.0 <= battery_level <= 1.0, "battery_level should be between 0 and 1"

            print("✅ Sensor structure validation successful against reference")
        else:
            print("⚠️ No sensor reference file found - basic validation only")

        print(f"Sensor info: {sensor_info}")

    @skip_if_no_serials
    async def test_get_info_controller_device(self, client: NetroClient, need_controller_reference) -> None: # pylint: disable=W0613
        """Test get_info with Netro controller device and validate against reference structure."""
        # Arrange - Controller serial from environment
        controller_key = NETRO_CTRL_SERIAL

        # Load reference structure (must exist for this integration test)
        reference_file = Path(__file__).parent / "reference_data" / "sprite_response.json"
        if not reference_file.exists():
            pytest.skip(f"Reference file missing: {reference_file}")
        with reference_file.open() as f:
            reference_data = json.load(f)

        # Act
        if controller_key is None:
            pytest.skip("NETRO_CTRL_SERIAL environment variable not set")
        result = await client.get_info(controller_key)

        # Assert - Verify controller response structure
        assert isinstance(result, dict)
        assert result["status"] == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        assert "device" in data, "Controller response should contain 'device' key"

        device_info = data["device"]
        assert device_info["serial"] == controller_key

        # Validate against reference structure if available
        if reference_data:
            print("🔍 Validating against reference structure...")
            reference_device = reference_data["data"]["device"]

            # Check that all expected fields from reference are present
            for field in reference_device.keys():
                assert field in device_info, f"Missing expected field: {field}"

            # Validate controller-specific fields
            assert device_info["serial"] == reference_device["serial"]
            assert "zone_num" in device_info, "Controller should have zone_num"
            assert "zones" in device_info, "Controller should have zones array"
            assert isinstance(device_info["zones"], list), "zones should be a list"
            assert len(device_info["zones"]) > 0, "Controller should have at least one zone"

            # Check zone structure
            for zone in device_info["zones"]:
                assert "name" in zone, "Zone should have name"
                assert "ith" in zone, "Zone should have ith (index)"
                assert "enabled" in zone, "Zone should have enabled status"
                assert "smart" in zone, "Zone should have smart mode"

            # Detect controller type (Sprite vs Pixie)
            controller_type = "Pixie" if "battery_level" in device_info else "Sprite"
            zone_count = device_info.get("zone_num", 0)

            print(f"✅ Controller type detected: {controller_type}")
            print(f"✅ Zone count: {zone_count}")
            print("✅ Structure validation successful against reference")
        else:
            print("⚠️ No reference file found - basic validation only")

        print(f"Controller response data keys: {list(data.keys())}")
        print(f"Device info keys: {list(device_info.keys())}")

        # Basic assertions
        assert isinstance(data, dict)
        assert len(data) > 0, "Controller response should contain data"

    @skip_if_no_serials
    async def test_compare_sensor_vs_controller_structure(self) -> None:
        """Compare the response structure between sensor and controller."""
        async with AiohttpClient() as http:
            client = NetroClient(http, NetroConfig())

            sensor_result = await client.get_info(NETRO_SENS_SERIAL)  # type: ignore

            controller_result = await client.get_info(NETRO_CTRL_SERIAL)  # type: ignore

            print("=== COMPARISON SENSOR vs CONTROLLER ===")

            # Both should have status OK
            assert sensor_result["status"] == "OK"
            assert controller_result["status"] == "OK"

            # Verify specific structures
            sensor_data = sensor_result["data"]
            controller_data = controller_result["data"]

            # Sensor has a 'sensor' key
            assert "sensor" in sensor_data
            assert "sensor" not in controller_data

            # Controller has a 'device' key
            assert "device" in controller_data
            assert "device" not in sensor_data

            # Verify sensor-specific fields
            sensor_info = sensor_data["sensor"]
            assert "battery_level" in sensor_info, "Sensor should have battery_level"
            assert "zone_num" not in sensor_info, "Sensor should not have zone_num"

            # Verify controller-specific fields
            controller_info = controller_data["device"]
            assert "zones" in controller_info, "Controller should have zones"
            assert "zone_num" in controller_info, "Controller should have zone_num"
            assert "battery_level" not in controller_info, (
                "Controller should not have battery_level"
            )

            print(f"✅ Sensor structure validated: {list(sensor_info.keys())}")
            print(f"✅ Controller structure validated: {list(controller_info.keys())}")
            print(f"✅ Controller has {controller_info['zone_num']} zones")

    async def test_get_info_invalid_key(self, client: NetroClient) -> None:
        """Test get_info with invalid API key."""
        invalid_key = "INVALID_KEY_123"

        with pytest.raises(NetroInvalidKey) as exc_info:
            await client.get_info(invalid_key)
        assert "Invalid key" in str(exc_info.value)

    @skip_if_no_serials
    async def test_get_info_response_time(self, client: NetroClient) -> None:
        """Test that the API responds within a reasonable time."""
        # Act
        start_time = time.time()
        result = await client.get_info(NETRO_SENS_SERIAL)  # type: ignore
        end_time = time.time()

        # Assert
        response_time = end_time - start_time
        assert response_time < 10.0, f"API too slow: {response_time:.2f}s"
        assert result["status"] == "OK"
        print(f"API response time: {response_time:.2f}s")

    @skip_if_no_serials
    async def test_get_info_with_custom_config(self) -> None:
        """Test with custom configuration."""
        # Arrange
        custom_config = NetroConfig(
            base_url="https://api.netrohome.com/npa/v1",  # Official URL
            default_timeout=15.0,
            extra_headers={"User-Agent": "PyNetro-Test/1.0"},
        )
        async with AiohttpClient() as http_client:
            client = NetroClient(http_client, custom_config)

            # Act
            result = await client.get_info(NETRO_SENS_SERIAL)  # type: ignore

            # Assert
            assert result["status"] == "OK"
            print(f"Response with custom config: {result}")

    @skip_if_no_serials
    async def test_get_schedules_controller_device(self, client: NetroClient, need_schedules_reference) -> None:  # pylint: disable=W0613
        """Test get_schedules with controller device and validate against reference structure."""
        # Arrange - Controller serial from environment and date range
        controller_key = NETRO_CTRL_SERIAL
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        zones = [1, 2]

        # Load reference structure (must exist for this integration test)
        reference_file = Path(__file__).parent / "reference_data" / "sprite_response_schedules.json"
        if not reference_file.exists():
            pytest.skip(f"Reference file missing: {reference_file}")
        with reference_file.open() as f:
            reference_data = json.load(f)

        # Act
        if controller_key is None:
            pytest.skip("NETRO_CTRL_SERIAL environment variable not set")
        result = await client.get_schedules(
            controller_key, start_date=start_date, end_date=end_date, zones=zones
        )

        # Assert - Verify schedules response structure
        assert isinstance(result, dict)
        assert result["status"] == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        assert "schedules" in data, "Response should contain 'schedules' key"

        schedules = data["schedules"]
        assert isinstance(schedules, list), "schedules should be a list"

        # Validate against reference structure if available
        if reference_data:
            print("🔍 Validating schedules against reference structure...")

            if schedules:  # Only validate if we have actual schedules
                # Check that schedule structure matches reference
                for schedule in schedules:
                    # Validate required fields based on reference structure
                    required_fields = [
                        "zone",
                        "id",
                        "status",
                        "source",
                        "start_time",
                        "end_time",
                        "local_date",
                        "local_start_time",
                        "local_end_time",
                    ]

                    for field in required_fields:
                        assert field in schedule, f"Missing required field: {field}"

                    # Validate zone is in requested zones (or any if no filter)
                    if zones:
                        # Note: API might return other zones too
                        assert isinstance(schedule["zone"], int), "Zone should be integer"

                    # Validate status values
                    valid_statuses = ["VALID", "EXECUTED", "CANCELLED", "EXPIRED"]
                    status = schedule["status"]
                    assert status in valid_statuses, f"Invalid status: {status}"

                    # Validate source values
                    valid_sources = ["SMART", "MANUAL", "SCHEDULED", "FIX"]
                    source = schedule["source"]
                    assert source in valid_sources, f"Invalid source: {source}"

                print(f"✅ Found {len(schedules)} schedules")
                print(f"✅ Date range: {start_date} to {end_date}")
                print(f"✅ Requested zones: {zones}")
                print("✅ Schedule structure validation successful against reference")
            else:
                print("i No schedules found for the requested period")

        else:
            print("⚠️ No reference file found - basic validation only")

        print(f"Schedules response data keys: {list(data.keys())}")
        print(f"Number of schedules: {len(schedules)}")
        if schedules:
            print(f"Sample schedule keys: {list(schedules[0].keys())}")

        # Basic assertions
        assert isinstance(data, dict)
        assert "schedules" in data

    @skip_if_no_serials
    async def test_get_moistures_controller_device(self, client: NetroClient, need_moistures_reference) -> None:  # pylint: disable=W0613
        """Test get_moistures with controller device and validate against reference structure."""
        # Arrange - Controller serial from environment and optional date range
        controller_key = NETRO_CTRL_SERIAL
        today = datetime.now()
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        zones = [1, 2]

        # Load reference structure (must exist for this integration test)
        reference_file = Path(__file__).parent / "reference_data" / "sprite_response_moistures.json"
        if not reference_file.exists():
            pytest.skip(f"Reference file missing: {reference_file}")
        with reference_file.open() as f:
            reference_data = json.load(f)

        # Act
        if controller_key is None:
            pytest.skip("NETRO_CTRL_SERIAL environment variable not set")
        result = await client.get_moistures(
            controller_key, start_date=start_date, end_date=end_date, zones=zones
        )

        # Assert - Verify moistures response structure
        assert isinstance(result, dict)
        assert result["status"] == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        # Expecting a key that contains moisture entries; be permissive to accept either "moistures" or "data" subkeys
        moisture_key = "moistures" if "moistures" in data else next((k for k in data.keys() if "moist" in k), None)
        assert moisture_key is not None, "Response should contain a moisture list (e.g. 'moistures')"

        moistures = data[moisture_key]
        assert isinstance(moistures, list), "moistures should be a list"

        # Validate against reference structure
        print("🔍 Validating moistures against reference structure...")

        if moistures:  # Only validate if we have actual records
            reference_moistures = reference_data["data"].get(moisture_key, []) if "data" in reference_data else []
            # Check required fields from reference (fallback to common keys)
            sample_ref = reference_moistures[0] if reference_moistures else (moistures[0] if moistures else {})
            required_fields = list(sample_ref.keys()) if isinstance(sample_ref, dict) else ["zone", "moisture", "time"]

            for entry in moistures:
                assert isinstance(entry, dict), "Each moisture entry should be a dict"
                for field in required_fields:
                    assert field in entry, f"Missing required field in moisture entry: {field}"

                # Validate zone is integer and moisture is numeric
                if "zone" in entry:
                    assert isinstance(entry["zone"], int), "zone should be integer"
                    if zones:
                        assert isinstance(entry["zone"], int), "zone should be integer"
                if "moisture" in entry:
                    assert isinstance(entry["moisture"], (int, float)), "moisture should be numeric"

            print(f"✅ Found {len(moistures)} moisture records")
            print(f"✅ Date range: {start_date} to {end_date}")
            print(f"✅ Requested zones: {zones}")
            print("✅ Moisture structure validation successful against reference")
        else:
            print("Info: No moisture records found for the requested period")

        print(f"Moistures response data keys: {list(data.keys())}")
        print(f"Number of moisture records: {len(moistures)}")
        if moistures:
            print(f"Sample moisture entry keys: {list(moistures[0].keys())}")

        # Basic assertions
        assert isinstance(data, dict)
        assert moisture_key in data

    @skip_if_no_serials
    async def test_get_events_controller_device(self, client: NetroClient, need_events_reference) -> None:  # pylint: disable=W0613
        """Test get_events with controller device and validate against reference structure."""
        # Arrange - Controller serial from environment and optional date range
        controller_key = NETRO_CTRL_SERIAL
        today = datetime.now()
        start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        # Load reference structure (must exist for this integration test)
        reference_file = Path(__file__).parent / "reference_data" / "sprite_response_events.json"
        if not reference_file.exists():
            pytest.skip(f"Reference file missing: {reference_file}")
        with reference_file.open() as f:
            reference_data = json.load(f)

        # Act
        if controller_key is None:
            pytest.skip("NETRO_CTRL_SERIAL environment variable not set")
        result = await client.get_events(controller_key, start_date=start_date, end_date=end_date)

        # Assert - Verify events response structure
        assert isinstance(result, dict)
        assert result.get("status") == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        # Determine events list key (accept 'events' or any key containing 'event')
        event_key = "events" if "events" in data else next((k for k in data.keys() if "event" in k), None)
        assert event_key is not None, "Response should contain an events list (e.g. 'events')"

        events = data[event_key]
        assert isinstance(events, list), "events should be a list"

        # Validate against reference structure if available
        if reference_data:
            print("🔍 Validating events against reference structure...")

            if events:  # Only validate if we have actual records
                reference_events = reference_data.get("data", {}).get(event_key, [])
                sample_ref = reference_events[0] if reference_events else (events[0] if events else {})
                required_fields = list(sample_ref.keys()) if isinstance(sample_ref, dict) else [
                    "id",
                    "zone",
                    "start_time",
                    "status",
                ]

                for entry in events:
                    assert isinstance(entry, dict), "Each event entry should be a dict"
                    for field in required_fields:
                        assert field in entry, f"Missing required field in event entry: {field}"

                    # Basic field type checks
                    if "zone" in entry:
                        assert isinstance(entry["zone"], int), "zone should be integer"
                    if "start_time" in entry:
                        assert isinstance(entry["start_time"], str), "start_time should be a string"

                print(f"✅ Found {len(events)} event records")
                print(f"✅ Date range: {start_date} to {end_date}")
                print("✅ Event structure validation successful against reference")
            else:
                print("ℹ️ No event records found for the requested period")  # noqa: RUF001
        else:
            print("⚠️ No reference file found - basic validation only")

        print(f"Events response data keys: {list(data.keys())}")
        print(f"Number of event records: {len(events)}")
        if events:
            print(f"Sample event entry keys: {list(events[0].keys())}")

        # Basic assertions
        assert isinstance(data, dict)
        assert event_key in data


# Diagnostic tests to understand the API structure
@pytest.mark.integration
@pytest.mark.diagnostic
class TestNetroAPIStructure:
    """Tests to understand and document the Netro API structure."""

    @skip_if_no_serials
    async def test_explore_api_response_structure(self) -> None:
        """Explore and document the complete API response structure."""
        async with AiohttpClient() as http_client:
            config = NetroConfig()
            client = NetroClient(http_client, config)

            result = await client.get_info(NETRO_SENS_SERIAL)  # type: ignore

            # Display complete structure for analysis
            print("=== COMPLETE API RESPONSE STRUCTURE ===")
            print(f"Type: {type(result)}")
            print(f"Main keys: {list(result.keys())}")

            for key, value in result.items():
                print(f"\n{key}: {type(value)}")
                if isinstance(value, dict):
                    print(f"  Sub-keys: {list(value.keys())}")
                elif isinstance(value, list) and value:
                    print(f"  First element: {type(value[0])}")
                    if isinstance(value[0], dict):
                        print(f"  First element keys: {list(value[0].keys())}")

            # Note: To save references, use tests/generate_references.py
            print("\n💡 To generate secure reference files, use:")
            print("   python tests/generate_references.py")

    @pytest.mark.postapi
    @pytest.mark.skipif(not NETRO_CTRL_SERIAL, reason="NETRO_CTRL_SERIAL not set")
    async def test_enable_controller(self) -> None:
        """Integration test: enable a Netro controller (real API call)."""
        async with AiohttpClient() as http_client:
            config = NetroConfig()
            client = NetroClient(http_client, config)
            result = await client.set_status(NETRO_CTRL_SERIAL, enabled=True) # type: ignore

            # Status check
            assert result["status"] == "OK"

            # Check meta fields
            meta = result.get("meta", {})
            assert "token_reset" in meta
            assert "token_limit" in meta
            assert "token_remaining" in meta
            assert "tid" in meta
            assert "version" in meta
            assert "last_active" in meta
            assert "time" in meta
            assert isinstance(meta["token_limit"], int)
            assert isinstance(meta["token_remaining"], int)
            assert meta["version"] == "1.0"

            # Check data field (may be empty but must exist)
            assert "data" in result
            assert isinstance(result["data"], dict)

    @pytest.mark.postapi
    @pytest.mark.skipif(not NETRO_CTRL_SERIAL, reason="NETRO_CTRL_SERIAL not set")
    async def test_disable_controller(self) -> None:
        """Integration test: disable a Netro controller (real API call)."""
        async with AiohttpClient() as http_client:
            config = NetroConfig()
            client = NetroClient(http_client, config)
            result = await client.set_status(NETRO_CTRL_SERIAL, enabled=False) # type: ignore

            # Status check
            assert result["status"] == "OK"

            # Check meta fields
            meta = result.get("meta", {})
            assert "token_reset" in meta
            assert "token_limit" in meta
            assert "token_remaining" in meta
            assert "tid" in meta
            assert "version" in meta
            assert "last_active" in meta
            assert "time" in meta
            assert isinstance(meta["token_limit"], int)
            assert isinstance(meta["token_remaining"], int)
            assert meta["version"] == "1.0"

            # Check data field (may be empty but must exist)
            assert "data" in result
            assert isinstance(result["data"], dict)
