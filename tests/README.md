# Tests for PyNetro

This folder contains the complete test suite for PyNetro with 16 tests (7 unit + 9 integration).

## 🏠 Netro Device Types

PyNetro supports three ty**💡 Tip**: Use `-s` when developing tests or debugging API responses to see all validation messages in real-time!

## 📁 Reference Data Files

The `tests/reference_data/` directory contains API response templates and real device data:

### 📋 **Template Files** (committed to git)
- `sensor_response_template.json` - Anonymized sensor structure  
- `sprite_response_template.json` - Anonymized Sprite controller structure
- `pixie_response_template.json` - Anonymized Pixie controller structure

### 🔒 **Real Data Files** (ignored by git for security)
- `sensor_response.json` - Your actual sensor data with real serial numbers
- `sprite_response.json` - Your actual Sprite controller data with real serial numbers

### 🔄 **Generating Real Reference Files**

```bash
# Set your device serial numbers
export NETRO_SENS_SERIAL="your_sensor_serial" 
export NETRO_CTRL_SERIAL="your_controller_serial"

# Generate reference files (automatically ignored by git)
python tests/generate_references.py
```

**Note**: Real reference files contain your actual device serial numbers and are automatically excluded from git for security.

## 📊 Coverage Reports of Netro devices with distinct characteristics:

### 🔋 **Sensor** 
- **Power**: Battery-powered  
- **Purpose**: Soil moisture and environmental monitoring
- **API Structure**: `{"data": {"sensor": {...}}}`
- **Key Fields**: `battery_level`, no zones

### 🎮 **Sprite Controller** 
- **Power**: AC-powered (plugged into wall)
- **Purpose**: Multi-zone irrigation control  
- **API Structure**: `{"data": {"device": {...}}}`
- **Key Fields**: `zone_num` > 1, `zones[]` array, no `battery_level`

### 🔌 **Pixie Controller**
- **Power**: Battery-powered (portable)
- **Purpose**: Single-zone irrigation control
- **API Structure**: `{"data": {"device": {...}}}`  
- **Key Fields**: `zone_num` = 1, `zones[]` with 1 element, `battery_level`

## 🔒 Security

⚠️ **Important**: Integration tests use environment variables to protect sensitive data (device serial numbers).

### Required Environment Variables

#### Method 1: .env file (recommended)

Create a `.env` file at the project root:

```bash
# Copy the template
cp .env.example .env

# Edit with your actual values
# .env
export NETRO_SENS_SERIAL=your_sensor_serial_number  
export NETRO_CTRL_SERIAL=your_controller_serial_number
```

Tests will automatically load this file! ✨

#### Method 2: Manual environment variables

```bash
export NETRO_SENS_SERIAL="your_sensor_serial_number"
export NETRO_CTRL_SERIAL="your_controller_serial_number"
```

## 🧪 Run All Tests

### Via Command Line

```bash
# All tests (unit + integration if variables are defined)
pytest tests/ -v

# With code coverage
pytest tests/ --cov=pynetro --cov-report=html

# With detailed execution times
pytest tests/ -v --durations=10
```

### Quick Commands

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/test_client.py -v

# Run integration tests only  
pytest tests/test_integration.py -v -m integration

# Run tests with coverage
pytest tests/ --cov=pynetro --cov-report=html
```

## 🔬 Unit Tests (always available)

```bash
# All unit tests
pytest tests/test_client.py -v

# Specific unit test
pytest tests/test_client.py::TestNetroClient::test_get_info_success -v

# Unit tests with coverage
pytest tests/test_client.py --cov=pynetro
```

## 🌐 Integration Tests (require environment variables)

```bash
# 1. Set environment variables
export NETRO_SENS_SERIAL="your_sensor_serial"
export NETRO_CTRL_SERIAL="your_controller_serial"

# 2. Run integration tests only
pytest tests/test_integration.py -v -m integration

# 3. Run with detailed output  
pytest tests/test_integration.py -v -s -m integration

# 4. Run specific integration test
pytest tests/test_integration.py::TestNetroIntegration::test_get_info_sensor_success -v -m integration
```

### Integration test behavior:
- **Variables defined** → Tests run against real Netro API
- **Variables missing** → Tests are **automatically skipped**
- **No errors** → Graceful handling with informative skip messages

## �️ Viewing Test Output and Debug Information

### The `-s` Option (Show Print Statements)

By default, pytest **captures and hides** all `print()` statements from passing tests. To see debug output:

```bash
# Show all print statements (recommended for debugging)
pytest tests/ -s -v

# Show prints for specific test
pytest tests/test_integration.py::TestNetroClientIntegration::test_get_info_controller_device -s -v

# Alternative syntax
pytest tests/ --capture=no -v
```

### When You See Prints

| Command | Passing Tests | Failing Tests |
|---------|---------------|---------------|
| `pytest` | ❌ Prints hidden | ✅ Prints shown in error report |
| `pytest -s` | ✅ Prints visible | ✅ Prints visible |

### Example Output with `-s`

```bash
pytest tests/test_integration.py -s -v
```

```
tests/test_integration.py::test_get_info_controller_device PASSED
🔍 Validating against reference structure...
✅ Controller type detected: Sprite
✅ Zone count: 6
✅ Structure validation successful against reference
Controller response data keys: ['device']
```

### Example Output without `-s`

```bash
pytest tests/test_integration.py -v
```

```
tests/test_integration.py::test_get_info_controller_device PASSED
```

**💡 Tip**: Use `-s` when developing tests or debugging API responses to see all validation messages in real-time!

## �📊 Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=pynetro --cov-report=html

# Open coverage report (generated in htmlcov/)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🏷️ Test Markers

Tests are organized with pytest markers:

```bash
# Unit tests only
pytest -m "not integration" -v

# Integration tests only  
pytest -m integration -v

# Diagnostic tests (for API exploration)
pytest -m diagnostic -v
```

## 📁 Test File Structure

```
tests/
├── README.md                    # This documentation
├── __init__.py                  # Test package marker
├── conftest.py                  # Global pytest configuration
├── test_client.py               # 5 unit tests with mocks
├── test_integration.py          # 9 integration tests with real HTTP
├── aiohttp_client.py           # HTTP client for integration tests
├── generate_references.py      # Tool to capture API responses
└── reference_data/             # API response templates and real data
    ├── README.md
    ├── sensor_response_template.json      # Anonymized sensor structure
    ├── sprite_response_template.json      # Anonymized Sprite controller
    ├── pixie_response_template.json       # Anonymized Pixie controller
    ├── sensor_response.json               # Real sensor data (git ignored)
    └── sprite_response.json               # Real Sprite data (git ignored)
```

## 🔍 Test Details

### Unit Tests (7 tests) - `test_client.py`
- **Always run** (no external dependencies)
- Use **MockHTTPClient** and **MockHTTPResponse** 
- Test **Protocol compliance** and **error handling**
- **100% predictable** results
- **Device-specific** tests using real API structure templates

**Tests included:**
1. `test_get_sprite_info_success` - Sprite controller (AC-powered, multi-zone)
2. `test_get_pixie_info_success` - Pixie controller (battery-powered, single-zone)
3. `test_get_sens_info_success` - Sensor device (battery-powered)
4. `test_get_info_api_error` - API error handling
5. `test_get_info_http_401` - HTTP 401 authentication errors
6. `test_get_info_generic_api_error` - Generic API errors
7. `test_get_info_custom_config` - Custom configuration testing

### Integration Tests (9 tests) - `test_integration.py`
- **Require environment variables** (auto-skipped if missing)
- Use **real aiohttp client** against **live Netro API**
- Test **actual device responses** and **network conditions**
- **Results depend on device state**

**Tests included:**
1. `test_get_info_sensor_device` - Sensor device validation against reference
2. `test_get_info_controller_device` - Controller device validation against reference
3. `test_compare_sensor_vs_controller_structure` - Structural differences validation
4. `test_get_info_real_api_success` - Real API success scenarios
5. `test_get_info_real_api_structure_validation` - Structure conformance
6. `test_get_info_invalid_key` - Invalid key error handling
7. `test_get_info_response_time` - Performance validation
8. `test_get_info_with_custom_config` - Custom configuration testing
9. `test_explore_api_response_structure` - API structure exploration

## 🚀 Quick Commands

```bash
# Quick test run (unit tests only)
pytest tests/test_client.py -v

# Full test run with coverage
pytest tests/ --cov=pynetro --cov-report=html -v

# Integration tests (if you have API keys)
pytest tests/test_integration.py -v -m integration

# Watch mode (runs tests on file changes)
pytest-watch tests/ 
```

## 🐛 Troubleshooting

### Tests not running
```bash
# Reinstall in development mode
pip install -e .

# Check pytest is installed
pytest --version
```

### Integration tests skipped
```bash
# Check environment variables are set
echo $NETRO_SENS_SERIAL $NETRO_CTRL_SERIAL

# Reload environment if using .env
source .env  # or restart terminal
```

### Import errors
```bash
# Ensure project is installed in development mode
pip install -e .

# Check Python path
python -c "import pynetro; print(pynetro.__file__)"
```

### Coverage not working
```bash
# Install coverage dependency
pip install pytest-cov

# Run with explicit source
pytest tests/ --cov=src/pynetro --cov-report=html
```

## 📋 Test Development Guidelines

### Adding Unit Tests
- Place in `test_client.py`
- Use `MockHTTPClient` and `MockHTTPResponse`
- Test **all error conditions**
- Ensure **100% predictable** results

### Adding Integration Tests  
- Place in `test_integration.py`
- Use `@pytest.mark.integration` decorator
- Add **environment variable checks**
- Handle **real API variability**

### Mock vs Real Testing Philosophy
- **Unit tests**: Fast, predictable, test logic
- **Integration tests**: Slow, variable, test real-world scenarios
- **Both are essential** for comprehensive coverage

## 🔧 Advanced Usage

### Running Specific Test Categories

```bash
# Only tests that require network
pytest -k "integration" -v

# Only mock-based tests
pytest -k "not integration" -v

# Tests for specific functionality
pytest -k "get_info" -v
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/ -n auto -v
```

### Test Output Control

```bash
# Minimal output
pytest tests/ -q

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Show locals on failure
pytest tests/ -l --tb=long
```