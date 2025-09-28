"""Integration tests for NetroClient with real HTTP client.

Ces tests nécessitent une vraie clé API Netro et une connexion internet.
Ils sont marqués comme 'integration' pour pouvoir les exécuter séparément.
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator

import pytest

from pynetro.client import NetroAuthError, NetroClient, NetroConfig, NetroError

from .aiohttp_client import AiohttpClient

# Variables d'environnement pour les tests d'intégration
NETRO_API_KEY = os.environ.get("NETRO_API_KEY")
NETRO_CTRL_SERIAL = os.environ.get("NETRO_CTRL_SERIAL")
NETRO_SENS_SERIAL = os.environ.get("NETRO_SENS_SERIAL")

# Skip integration tests if required environment variables are not provided
skip_if_no_key = pytest.mark.skipif(
    not NETRO_API_KEY,
    reason="NETRO_API_KEY environment variable not set"
)

skip_if_no_serials = pytest.mark.skipif(
    not (NETRO_CTRL_SERIAL and NETRO_SENS_SERIAL),
    reason="NETRO_CTRL_SERIAL and/or NETRO_SENS_SERIAL environment variables not set"
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
    async def client(
        self, real_http_client: AiohttpClient, config: NetroConfig
    ) -> NetroClient:
        """Provide a NetroClient with real HTTP client."""
        return NetroClient(real_http_client, config)

    @skip_if_no_serials
    async def test_get_info_sensor_device(self, client: NetroClient) -> None:
        """Test get_info with Netro sensor device."""
        # Arrange - Sensor serial from environment
        sensor_key = NETRO_SENS_SERIAL

        # Act
        result = await client.get_info(sensor_key)

        # Assert - Vérifier la structure de la réponse sensor
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

        print(f"Sensor info: {sensor_info}")

    @skip_if_no_serials
    async def test_get_info_controller_device(self, client: NetroClient) -> None:
        """Test get_info with Netro controller device."""
        # Arrange - Controller serial from environment
        controller_key = NETRO_CTRL_SERIAL

        # Act
        result = await client.get_info(controller_key)

        # Assert - Vérifier la structure de la réponse controller
        assert isinstance(result, dict)
        assert result["status"] == "OK"
        assert "data" in result
        assert "meta" in result

        data = result["data"]
        # Les controllers peuvent avoir une structure différente des sensors
        print(f"Controller response data keys: {list(data.keys())}")
        print(f"Controller full response: {result}")

        # Assertions basiques - nous découvrirons la structure exacte
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

            # Vérifier les structures spécifiques
            sensor_data = sensor_result["data"]
            controller_data = controller_result["data"]

            # Sensor a une clé 'sensor'
            assert "sensor" in sensor_data
            assert "sensor" not in controller_data

            # Controller a une clé 'device'
            assert "device" in controller_data
            assert "device" not in sensor_data

            # Vérifier les champs spécifiques du sensor
            sensor_info = sensor_data["sensor"]
            assert "battery_level" in sensor_info, "Sensor should have battery_level"
            assert "zone_num" not in sensor_info, "Sensor should not have zone_num"

            # Vérifier les champs spécifiques du controller
            controller_info = controller_data["device"]
            assert "zones" in controller_info, "Controller should have zones"
            assert "zone_num" in controller_info, "Controller should have zone_num"
            assert (
                "battery_level" not in controller_info
            ), "Controller should not have battery_level"

            print(f"✅ Sensor structure validated: {list(sensor_info.keys())}")
            print(f"✅ Controller structure validated: {list(controller_info.keys())}")
            print(f"✅ Controller has {controller_info['zone_num']} zones")

    @skip_if_no_serials
    async def test_get_info_real_api_success(self, client: NetroClient) -> None:
        """Test get_info with real Netro API - generic success case."""
        # Act - Use sensor by default
        result = await client.get_info(NETRO_SENS_SERIAL)

        # Assert - Vérifier la structure de la réponse
        assert isinstance(result, dict)
        assert "status" in result
        assert result["status"] == "OK"

        # Vérifier que les sections attendues sont présentes
        assert "data" in result
        data = result["data"]

        # La structure exacte peut varier selon le compte, mais certains champs sont standards
        assert isinstance(data, dict)
        print(f"Réponse API réelle reçue: {result}")

    @skip_if_no_serials
    async def test_get_info_real_api_structure_validation(
        self, client: NetroClient
    ) -> None:
        """Test que la structure de la réponse correspond à nos attentes."""
        # Act
        result = await client.get_info(NETRO_SENS_SERIAL)

        # Assert - Validation de structure plus détaillée
        assert isinstance(result, dict)

        # Vérifier l'enveloppe API Netro
        required_top_level = ["status"]
        for field in required_top_level:
            assert field in result, f"Champ manquant: {field}"

        # Si status = OK, data devrait être présent
        if result["status"] == "OK":
            assert "data" in result
            data = result["data"]
            assert isinstance(data, dict)

            # Vérifier quelques champs communs (selon la doc Netro)
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
        """Test avec une configuration personnalisée."""
        # Arrange
        custom_config = NetroConfig(
            base_url="https://api.netrohome.com/npa/v1",  # URL officielle
            default_timeout=15.0,
            extra_headers={"User-Agent": "PyNetro-Test/1.0"}
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

            # Note: Pour sauvegarder des références, utilisez tests/generate_references.py
            print("\n💡 Pour générer des fichiers de référence sécurisés, utilisez:")
            print("   python tests/generate_references.py")
