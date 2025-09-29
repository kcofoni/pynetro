#!/usr/bin/env python3
"""Script to generate JSON reference files for Netro API responses.

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

# Environment variables for serial numbers
NETRO_SENS_SERIAL = os.getenv("NETRO_SENS_SERIAL")
NETRO_CTRL_SERIAL = os.getenv("NETRO_CTRL_SERIAL")


async def generate_all_references() -> None:
    """Generate all JSON reference files."""
    # Check that environment variables are defined
    if not NETRO_SENS_SERIAL or not NETRO_CTRL_SERIAL:
        print("❌ Missing environment variables:")
        print("   NETRO_SENS_SERIAL and NETRO_CTRL_SERIAL must be defined")
        print("   Example: export NETRO_SENS_SERIAL='your_sensor_serial'")
        print("   Example: export NETRO_CTRL_SERIAL='your_controller_serial'")
        return

    reference_dir = Path(__file__).parent / "reference_data"
    reference_dir.mkdir(exist_ok=True)

    async with AiohttpClient() as http:
        client = NetroClient(http, NetroConfig())

        print("📡 Generating Netro API references...")

        # Generate sensor reference
        print("  🔋 Retrieving sensor data...")
        sensor_result = await client.get_info(NETRO_SENS_SERIAL)
        sensor_file = reference_dir / "sensor_response.json"
        with sensor_file.open("w") as f:
            json.dump(sensor_result, f, indent=2, default=str)
        print(f"  ✅ Sensor: {sensor_file}")

        # Generate controller reference
        print("  🎮 Retrieving controller data...")
        controller_result = await client.get_info(NETRO_CTRL_SERIAL)
        controller_file = reference_dir / "controller_response.json"
        with controller_file.open("w") as f:
            json.dump(controller_result, f, indent=2, default=str)
        print(f"  ✅ Controller: {controller_file}")

        print("\n📊 Summary of generated structures:")
        print(f"  Sensor data keys: {list(sensor_result['data'].keys())}")
        print(f"  Controller data keys: {list(controller_result['data'].keys())}")
        print(f"  Sensor fields: {list(sensor_result['data']['sensor'].keys())}")
        print(f"  Controller fields: {list(controller_result['data']['device'].keys())}")


def load_sensor_reference() -> dict:
    """Load the sensor reference file.

    Returns the real sensor data if available, otherwise suggests generation.
    """
    reference_file = Path(__file__).parent / "reference_data" / "sensor_response.json"
    if not reference_file.exists():
        print(f"❌ Reference file not found: {reference_file}")
        print("💡 Run: python tests/generate_references.py")
        print("📖 Or use template: tests/reference_data/sensor_response_template.json")
        return {}

    with reference_file.open() as f:
        return json.load(f)


def load_controller_reference() -> dict:
    """Load the controller reference file.

    Returns the real controller data if available, otherwise suggests generation.
    """
    reference_file = Path(__file__).parent / "reference_data" / "controller_response.json"
    if not reference_file.exists():
        print(f"❌ Reference file not found: {reference_file}")
        print("💡 Run: python tests/generate_references.py")
        print("📖 Or use template: tests/reference_data/controller_response_template.json")
        return {}

    with reference_file.open() as f:
        return json.load(f)


if __name__ == "__main__":
    asyncio.run(generate_all_references())
