# pynetro

Async Python wrapper for Netro API — HTTP-agnostic (works with adapters).
Designed to integrate with Home Assistant but usable anywhere.

## Installation

### 🚀 Quick Installation

```bash
# Clone the project
git clone https://github.com/kcofoni/pynetro.git
cd pynetro

# Install in development mode
pip install -e .
```

### 🛠️ Complete Development Setup

#### 1. Prerequisites
- Python 3.10 or higher
- git

#### 2. Environment Setup

```bash
# Clone the project
git clone https://github.com/kcofoni/pynetro.git
cd pynetro

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# Verify the environment is activated (prompt should show (.venv))
which python  # Should point to .venv/bin/python
```

#### 3. Install Dependencies

```bash
# Install the project in development mode
pip install -e .

# Install development dependencies (tests, linting, etc.)
pip install -r requirements-dev.txt
```

#### 4. Verify Installation

```bash
# Run unit tests to verify everything works
pytest tests/test_client.py -v

# Check linting
ruff check src/ tests/
```

### 🧪 Testing

Run tests using pytest commands:

#### 5. Integration Tests Configuration (optional)

```bash
# Create an .env file with your Netro device serial numbers
cp .env.example .env
# Then edit .env with your actual values

# Generate reference files for development (contains real serial numbers, ignored by git)
python tests/generate_references.py

# Test integrations (requires internet connection and Netro devices)
pytest tests/test_integration.py -v -m integration
```

**Security Note**: Reference files are automatically ignored by git as they contain real device serial numbers. Template files with anonymized data are provided for understanding the API structure.

### 🔧 Common Troubleshooting

#### Virtual environment not activated
```bash
# Check that the environment is activated
which python  # Should point to .venv/bin/python
echo $VIRTUAL_ENV  # Should display the path to .venv

# If not activated:
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

#### Import errors during tests
```bash
# Reinstall the project in development mode
pip install -e .
```

#### Integration tests skipped
```bash
# Integration tests require environment variables
export NETRO_SENS_SERIAL="your_sensor_serial"
export NETRO_CTRL_SERIAL="your_controller_serial"

# Verify variables are set
echo $NETRO_SENS_SERIAL $NETRO_CTRL_SERIAL
```

### Tests

The project has a comprehensive test suite with 14 tests (7 unit + 7 integration).

```bash
# Run all tests
pytest tests/ -v

# Unit tests only (always available)
pytest tests/test_client.py -v

# Integration tests (require environment variables)
pytest tests/test_integration.py -v -m integration
```

📚 **Complete testing documentation**: See [`tests/README.md`](tests/README.md) for all commands and advanced options.

## Security & Reference Files

For security reasons, files containing real device serial numbers are automatically ignored by git:
- `tests/reference_data/sensor_response.json` 
- `tests/reference_data/sprite_response.json`

**What's available for fresh clones:**
- ✅ Anonymized templates showing API structure (`*_template.json`)
- ✅ Generation script to create real reference files when needed
- ✅ All functionality works without these files - they're optional documentation

**If you need the real reference files:**
```bash
# Set your device serial numbers
export NETRO_SENS_SERIAL="your_sensor_serial" 
export NETRO_CTRL_SERIAL="your_controller_serial"

# Generate the files (will be ignored by git)
python tests/generate_references.py
```
