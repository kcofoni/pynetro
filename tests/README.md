# Tests for PyNetro

This folder contains the complete test suite for PyNetro with 14 tests (5 unit + 9 integration).

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

## 📊 Coverage Reports

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
└── reference_data/             # Captured API responses
    ├── README.md
    ├── sensor_info_response.json
    └── controller_info_response.json
```

## 🔍 Test Details

### Unit Tests (5 tests) - `test_client.py`
- **Always run** (no external dependencies)
- Use **MockHTTPClient** and **MockHTTPResponse** 
- Test **Protocol compliance** and **error handling**
- **100% predictable** results

**Tests included:**
1. `test_get_info_success` - Successful API response
2. `test_get_info_http_error` - HTTP error handling
3. `test_get_info_json_error` - Invalid JSON handling
4. `test_get_info_missing_key` - Missing response keys
5. `test_get_info_unexpected_error` - Unexpected exceptions

### Integration Tests (9 tests) - `test_integration.py`
- **Require environment variables** (auto-skipped if missing)
- Use **real aiohttp client** against **live Netro API**
- Test **actual device responses** and **network conditions**
- **Results depend on device state**

**Tests included:**
1. `test_get_info_sensor_success` - Sensor device info
2. `test_get_info_controller_success` - Controller device info  
3. `test_get_info_different_serials` - Different device types
4. `test_get_info_network_conditions` - Network reliability
5. `test_get_info_response_structure` - API response validation
6. `test_multiple_requests_consistency` - Multiple calls
7. `test_error_handling_invalid_serial` - Invalid device serial
8. `test_concurrent_requests` - Concurrent API calls
9. `test_environment_variable_security` - Security validation

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