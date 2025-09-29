"""Integration tests for NetroClient with real HTTP client.

Ces tests nécessitent une vraie clé API Netro et une connexion internet.
Ils sont marqués comme 'integration' pour pouvoir les exécuter séparément.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from pynetro.client import NetroAuthError, NetroClient, NetroConfig, NetroError

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
    async def test_get_info_sensor_device(self, client: NetroClient) -> None:
        """Test get_info with Netro sensor device and validate against reference structure."""
        # Arrange - Sensor serial from environment
        sensor_key = NETRO_SENS_SERIAL

        # Load reference structure
        reference_file = Path(__file__).parent / "reference_data" / "sensor_response.json"
        reference_data = None
        if reference_file.exists():
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
            battery_level = sensor_info["battery_level"]
            assert isinstance(battery_level, (int, float)), "battery_level should be numeric"
            assert 0.0 <= battery_level <= 1.0, "battery_level should be between 0 and 1"

            print("✅ Sensor structure validation successful against reference")
        else:
            print("⚠️ No sensor reference file found - basic validation only")

        print(f"Sensor info: {sensor_info}")

    @skip_if_no_serials
    async def test_get_info_controller_device(self, client: NetroClient) -> None:
        """Test get_info with Netro controller device and validate against reference structure."""
        # Arrange - Controller serial from environment
        controller_key = NETRO_CTRL_SERIAL

        # Load reference structure
        reference_file = Path(__file__).parent / "reference_data" / "sprite_response.json"
        reference_data = None
        if reference_file.exists():
            with reference_file.open() as f:
                reference_data = json.load(f)

        # Act
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

            # Test sensor
            sensor_result = await client.get_info(NETRO_SENS_SERIAL)

            # Test controller
            controller_result = await client.get_info(NETRO_CTRL_SERIAL)

            print("=== COMPARISON SENSOR vs CONTROLLER ===")

            # Les deux devraient avoir status OK
            assert sensor_result["status"] == "OK"
            assert controller_result["status"] == "OK"

            # Verify specific structures
            sensor_data = sensor_result["data"]
            controller_data = controller_result["data"]

            # Sensor a une clé 'sensor'
            assert "sensor" in sensor_data
            assert "sensor" not in controller_data

            # Controller a une clé 'device'
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

    @skip_if_no_serials
    async def test_get_info_real_api_success(self, client: NetroClient) -> None:
        """Test get_info with real Netro API - generic success case."""
        # Act - Use sensor by default
        result = await client.get_info(NETRO_SENS_SERIAL)

        # Assert - Verify response structure
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "OK"

        # Verify that expected sections are present
        assert "data" in result
        data = result["data"]

        # La structure exacte peut varier selon le compte, mais certains champs sont standards
        assert isinstance(data, dict)
        print(f"Réponse API réelle reçue: {result}")

    @skip_if_no_serials
    async def test_get_info_real_api_structure_validation(self, client: NetroClient) -> None:
        """Test que la structure de la réponse correspond à nos attentes."""
        # Act
        result = await client.get_info(NETRO_SENS_SERIAL)

        # Assert - Validation de structure plus détaillée
        assert isinstance(result, dict)

        # Verify Netro API envelope
        required_top_level = ["status"]
        for field in required_top_level:
            assert field in result, f"Champ manquant: {field}"

        # Si status = OK, data devrait être présent
        if result["status"] == "OK":
            assert "data" in result
            data = result["data"]
            assert isinstance(data, dict)

            # Verify some common fields (according to Netro docs)
            # Note: la structure exacte dépend de votre compte
            print(f"Structure des données: {list(data.keys())}")

    async def test_get_info_invalid_key(self, client: NetroClient) -> None:
        """Test get_info with invalid API key."""
        invalid_key = "INVALID_KEY_123"

        # Act & Assert
        with pytest.raises((NetroAuthError, NetroError)) as exc_info:
            await client.get_info(invalid_key)

        print(f"Erreur reçue avec clé invalide: {exc_info.value}")

    @skip_if_no_serials
    async def test_get_info_response_time(self, client: NetroClient) -> None:
        """Test que l'API répond dans un délai raisonnable."""
        # Act
        start_time = time.time()
        result = await client.get_info(NETRO_SENS_SERIAL)
        end_time = time.time()

        # Assert
        response_time = end_time - start_time
        assert response_time < 10.0, f"API trop lente: {response_time:.2f}s"
        assert result["status"] == "OK"
        print(f"Temps de réponse API: {response_time:.2f}s")

    @skip_if_no_serials
    async def test_get_info_with_custom_config(self) -> None:
        """Test with custom configuration."""
        # Arrange
        custom_config = NetroConfig(
            base_url="https://api.netrohome.com/npa/v1",  # URL officielle
            default_timeout=15.0,
            extra_headers={"User-Agent": "PyNetro-Test/1.0"},
        )

        async with AiohttpClient() as http_client:
            client = NetroClient(http_client, custom_config)

            # Act
            result = await client.get_info(NETRO_SENS_SERIAL)

            # Assert
            assert result["status"] == "OK"
            print(f"Réponse avec config personnalisée: {result}")


# Tests de diagnostic pour comprendre la structure de l'API
@pytest.mark.integration
@pytest.mark.diagnostic
class TestNetroAPIStructure:
    """Tests pour comprendre et documenter la structure de l'API Netro."""

    @skip_if_no_serials
    async def test_explore_api_response_structure(self) -> None:
        """Explorer et documenter la structure complète de la réponse API."""
        async with AiohttpClient() as http_client:
            config = NetroConfig()
            client = NetroClient(http_client, config)

            result = await client.get_info(NETRO_SENS_SERIAL)

            # Afficher la structure complète pour analyse
            print("=== STRUCTURE COMPLÈTE DE LA RÉPONSE API ===")
            print(f"Type: {type(result)}")
            print(f"Clés principales: {list(result.keys())}")

            for key, value in result.items():
                print(f"\n{key}: {type(value)}")
                if isinstance(value, dict):
                    print(f"  Sous-clés: {list(value.keys())}")
                elif isinstance(value, list) and value:
                    print(f"  Premier élément: {type(value[0])}")
                    if isinstance(value[0], dict):
                        print(f"  Clés du premier élément: {list(value[0].keys())}")

            # Note: To save references, use tests/generate_references.py
            print("\n💡 To generate secure reference files, use:")
            print("   python tests/generate_references.py")
