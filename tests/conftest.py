"""Global pytest configuration to automatically load environment variables."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


def pytest_configure(config):  # pylint: disable=unused-argument
    """Automatic pytest configuration."""
    # Load .env file if it exists (look in project root)
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        try:
            load_dotenv(env_file)
            print(f"✅ Environment variables loaded from {env_file}")
        except ImportError:
            # Fallback: manually parse the .env file
            _load_env_manually(env_file)
            print(f"✅ Environment variables loaded manually from {env_file}")


def _load_env_manually(env_file: Path) -> None:
    """Manually load a simple .env file (fallback without python-dotenv)."""
    with env_file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle formats: KEY=value and export KEY=value
                if line.startswith('export '):
                    line = line[7:]  # Remove 'export '

                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value


@pytest.fixture(scope="session", autouse=True)
def load_environment():
    """Fixture to ensure environment variables are loaded."""
    # This fixture is automatically executed at the start of each test session
    sens_serial = os.getenv("NETRO_SENS_SERIAL")
    ctrl_serial = os.getenv("NETRO_CTRL_SERIAL")

    if sens_serial and ctrl_serial:
        print(f"🔧 Integration tests enabled (SENS: {sens_serial[:4]}..., "
              f"CTRL: {ctrl_serial[:4]}...)")
    else:
        print("⚠️ Integration tests disabled (missing environment variables)")
