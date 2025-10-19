"""Global pytest configuration to automatically load environment variables."""

import os
import shutil
import subprocess
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
    """Fixture to ensure environment variables are loaded.

    If expected serials are missing from the environment, attempt to load a .env
    file from the project root (using python-dotenv if available, otherwise the
    fallback _load_env_manually). Re-check env vars after loading.
    """
    sens_serial = os.getenv("NETRO_SENS_SERIAL")
    ctrl_serial = os.getenv("NETRO_CTRL_SERIAL")

    if not (sens_serial and ctrl_serial):
        # try to load .env from project root (same logic as pytest_configure)
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            try:
                load_dotenv(env_file)
                print(f"ℹ️ Loaded environment from {env_file}")  # noqa: RUF001
            except Exception:  # pylint: disable=broad-except
                _load_env_manually(env_file)
                print(f"ℹ️ Loaded environment (manual) from {env_file}")  # noqa: RUF001

            # re-read after loading
            sens_serial = os.getenv("NETRO_SENS_SERIAL")
            ctrl_serial = os.getenv("NETRO_CTRL_SERIAL")

    if sens_serial and ctrl_serial:
        print(f"🔧 Integration tests enabled (SENS: {sens_serial[:4]}..., CTRL: {ctrl_serial[:4]}...)")
    else:
        print("⚠️ Integration tests disabled (missing environment variables)")

REF_DIR = Path(__file__).parent / "reference_data"
SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "generate_reference.py"


def _call_generate_script(template: Path, target: Path, serial: str) -> None:
    """Call the project's generate_reference.py script if present.

    If the script is available, it is invoked to generate the reference; otherwise a
    simple placeholder replacement from the template into the target file is performed.
    """
    try:
        if SCRIPT_PATH.exists():
            subprocess.run(
                ["python", str(SCRIPT_PATH), str(template), str(target), serial],
                check=True,
            )
            print(f"Generated reference {target} using script {SCRIPT_PATH}")
            return
    except subprocess.CalledProcessError as exc:
        # If the script fails, raise so pytest will report the issue
        msg = f"Reference generation script failed: {exc}"
        raise RuntimeError(msg) from exc

    # Fallback: naive text replacement of common dummy tokens
    text = template.read_text(encoding="utf-8")
    replacements = {
        "DUMMY_SERIAL": serial,
        "000000000000": serial,
        "SENSOR_SERIAL": serial,
        "CTRL_SERIAL": serial,
    }
    for k, v in replacements.items():
        if k in text:
            text = text.replace(k, v)
    target.write_text(text, encoding="utf-8")
    print(f"Generated reference {target} by template substitution")


def ensure_reference(
    ref_name: str,
    template_name: str | None = None,
    serial_env: str | None = None,
    copy_if_template: bool = False,
) -> None:
    """Ensure a reference file exists for tests.

    Rules:
    - If reference exists -> do nothing.
    - Else if template exists:
        - If serial_env provided and env var set -> generate from template (replace serial).
        - Elif copy_if_template True -> copy template to reference (no serial replacement).
        - Else -> skip the test (serial required).
    - Else -> skip the test.
    """
    REF_DIR.mkdir(parents=True, exist_ok=True)
    ref = REF_DIR / ref_name
    if ref.exists():
        return

    tpl = REF_DIR / template_name if template_name else None
    if tpl and tpl.exists():
        # If a serial is required for generation
        if serial_env:
            serial = os.getenv(serial_env)
            if not serial:
                pytest.skip(f"Reference {ref_name} missing and environment {serial_env} not set")
            # Only generate if target missing (do not overwrite existing ref)
            _call_generate_script(tpl, ref, serial)
            return
        # If we can copy template directly into reference (no serials inside)
        if copy_if_template:
            shutil.copy(tpl, ref)
            print(f"Copied template {tpl} to reference {ref}")
            return
        pytest.skip(f"Reference {ref_name} missing and no generation rule configured")
    else:
        pytest.skip(f"Reference {ref_name} missing and template {template_name} not found")


# Fixtures for tests to request as needed
@pytest.fixture
def need_sensor_reference():  # noqa: D103 # pylint: disable=C0116
    ensure_reference(
        "sensor_response.json",
        template_name="sensor_response_template.json",
        serial_env="NETRO_SENS_SERIAL",
    )


@pytest.fixture
def need_controller_reference():  # noqa: D103 # pylint: disable=C0116
    ensure_reference(
        "sprite_response.json",
        template_name="sprite_response_template.json",
        serial_env="NETRO_CTRL_SERIAL",
    )


@pytest.fixture
def need_schedules_reference():  # noqa: D103 # pylint: disable=C0116
    # schedules templates do not include serials; copy template if ref missing
    ensure_reference(
        "sprite_response_schedules.json",
        template_name="sprite_response_schedules_template.json",
        copy_if_template=True,
    )


@pytest.fixture
def need_moistures_reference():  # noqa: D103 # pylint: disable=C0116
    ensure_reference(
        "sprite_response_moistures.json",
        template_name="sprite_response_moistures_template.json",
        copy_if_template=True,
    )


@pytest.fixture
def need_events_reference():  # noqa: D103 # pylint: disable=C0116
    ensure_reference(
        "sprite_response_events.json",
        template_name="sprite_response_events_template.json",
        copy_if_template=True,
    )


@pytest.fixture
def need_sensor_data_reference():  # pylint: disable=C0116
    """Ensure sensor_response_data.json exists (copy from template if present)."""
    ensure_reference(
        "sensor_response_data.json",
        template_name="sensor_response_data_template.json",
        copy_if_template=True,
    )
