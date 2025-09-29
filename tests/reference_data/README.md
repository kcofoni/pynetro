# Netro API Response Reference

This directory contains reference response structures for Netro Public API v1.

## Reference Files

### `sensor_response.json`
Typical response for a Netro **sensor** device (e.g., humidity sensor).

**Structure**:
```json
{
  "status": "OK",
  "meta": { ... },
  "data": {
    "sensor": {
      "name": "Sensor Name",
      "serial": "34******a4",  // Replace with your serial number
      "status": "ONLINE|OFFLINE",
      "version": "3.1",
      "sw_version": "3.1.3", 
      "last_active": "2025-09-28T17:03:26",
      "battery_level": 0.63
    }
  }
}
```

**Sensor-specific fields**:
- `battery_level`: Battery level (0.0 to 1.0)

### `sprite_response.json`
Typical response for a Netro **controller** device (e.g., irrigation controller).

**Structure**:
```json
{
  "status": "OK", 
  "meta": { ... },
  "data": {
    "device": {
      "name": "Controller Name",
      "serial": "YYYYYYYYYYYY",  // Replace with your serial number
      "status": "ONLINE|OFFLINE",
      "version": "1.2",
      "sw_version": "1.1.1",
      "last_active": "2025-09-28T17:28:58",
      "zone_num": 6,
      "zones": [
        {
          "name": "Zone 1",
          "ith": 1,
          "enabled": true,
          "smart": "SMART"
        }
      ]
    }
  }
}
```

**Controller-specific fields**:
- `zone_num`: Number of irrigation zones
- `zones[]`: List of configured zones

## Usage in Tests

These files are used as reference for:
- Validating response structures in integration tests
- Documenting differences between sensor and controller
- Creating realistic mocks in unit tests

## Files in this directory

### Template files (committed to git):
- `sensor_response_template.json` - Anonymized sensor response structure
- `sprite_response_template.json` - Anonymized Sprite controller (AC-powered) response structure
- `pixie_response_template.json` - Anonymized Pixie controller (battery-powered) response structure

### Real response files (ignored by git):
- `sensor_response.json` - Real sensor data with your serial numbers
- `sprite_response.json` - Real Sprite controller data with your serial numbers

## Generation

Real response files are automatically generated when you have environment variables set:

```bash
# Set your device serial numbers
export NETRO_SENS_SERIAL="your_sensor_serial"
export NETRO_CTRL_SERIAL="your_controller_serial"

# Generate real response files (will be ignored by git)
python -c "from tests.generate_references import generate_all_references; import asyncio; asyncio.run(generate_all_references())"
```

**Note**: The real response files contain your actual device serial numbers and are automatically ignored by git for security.

Last updated: September 29, 2025