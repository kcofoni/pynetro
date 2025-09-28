#!/usr/bin/env python3
"""Script pour générer les fichiers de référence JSON des réponses API Netro.

Usage:
    python tests/generate_references.py

Ou depuis un autre script:
    from tests.generate_references import generate_all_references
    await generate_all_references()
"""

import asyncio
import json
import os
from pathlib import Path

from pynetro.client import NetroClient, NetroConfig

from .aiohttp_client import AiohttpClient

# Variables d'environnement pour les numéros de série
NETRO_SENS_SERIAL = os.getenv("NETRO_SENS_SERIAL")
NETRO_CTRL_SERIAL = os.getenv("NETRO_CTRL_SERIAL")


async def generate_all_references() -> None:
    """Génère tous les fichiers de référence JSON."""
    # Vérifier que les variables d'environnement sont définies
    if not NETRO_SENS_SERIAL or not NETRO_CTRL_SERIAL:
        print("❌ Variables d'environnement manquantes:")
        print("   NETRO_SENS_SERIAL et NETRO_CTRL_SERIAL doivent être définies")
        print("   Exemple: export NETRO_SENS_SERIAL='votre_serial_sensor'")
        print("   Exemple: export NETRO_CTRL_SERIAL='votre_serial_controller'")
        return

    reference_dir = Path(__file__).parent / "reference_data"
    reference_dir.mkdir(exist_ok=True)

    async with AiohttpClient() as http:
        client = NetroClient(http, NetroConfig())

        print("📡 Génération des références API Netro...")

        # Générer référence sensor
        print("  🔋 Récupération données sensor...")
        sensor_result = await client.get_info(NETRO_SENS_SERIAL)
        sensor_file = reference_dir / "sensor_response.json"
        with sensor_file.open("w") as f:
            json.dump(sensor_result, f, indent=2, default=str)
        print(f"  ✅ Sensor: {sensor_file}")

        # Générer référence controller
        print("  🎮 Récupération données controller...")
        controller_result = await client.get_info(NETRO_CTRL_SERIAL)
        controller_file = reference_dir / "controller_response.json"
        with controller_file.open("w") as f:
            json.dump(controller_result, f, indent=2, default=str)
        print(f"  ✅ Controller: {controller_file}")

        print("\n📊 Résumé des structures générées:")
        print(f"  Sensor data keys: {list(sensor_result['data'].keys())}")
        print(f"  Controller data keys: {list(controller_result['data'].keys())}")
        print(f"  Sensor fields: {list(sensor_result['data']['sensor'].keys())}")
        print(f"  Controller fields: {list(controller_result['data']['device'].keys())}")


def load_sensor_reference() -> dict:
    """Charge le fichier de référence sensor."""
    reference_file = Path(__file__).parent / "reference_data" / "sensor_response.json"
    with reference_file.open() as f:
        return json.load(f)


def load_controller_reference() -> dict:
    """Charge le fichier de référence controller."""
    reference_file = Path(__file__).parent / "reference_data" / "controller_response.json"
    with reference_file.open() as f:
        return json.load(f)


if __name__ == "__main__":
    asyncio.run(generate_all_references())
