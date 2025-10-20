# pynetro

Async Python wrapper for the Netro API — HTTP-agnostic.

[Netro Public API](https://www.netrohome.com/en/shop/articles/10)

## Installation

### Quick install

```bash
git clone https://github.com/kcofoni/pynetro.git
cd pynetro
pip install -e .
```

### Development setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
```

2. Install the package and dev dependencies:

```bash
pip install -e .
pip install -r requirements-dev.txt
```

3. Verify basic checks:

```bash
# run unit tests
pytest tests/test_client.py -v

# lint
ruff check src/ tests/
```

## Testing

This project provides two kinds of tests:

- Unit tests
  - Fast, offline, no network required.
  - Located mainly in `tests/test_client.py`.
  - Run locally or in CI without environment variables.

- Integration tests
  - Interact with the Netro API (or rely on prepared reference responses).
  - Marked with `@pytest.mark.integration` in `tests/test_integration.py`.
  - Require device serial numbers and/or reference files.

Running tests:

```bash
# run all tests
pytest tests/ -v

# unit tests only
pytest tests/test_client.py -v

# integration tests (requires env vars / references)
pytest tests/test_integration.py -m integration -v
```

### Reference files & templates

- Sensitive reference files that include real serials are NOT committed.
- Committed templates live under `tests/reference_data/*_template.json`.
- The test helpers in `tests/conftest.py` expose fixtures (e.g. `need_sensor_reference`, `need_controller_reference`, `need_sensor_data_reference`) that:
  - If a reference file already exists, use it unchanged.
  - If the reference is missing but a template exists:
    - If a serial env var is provided (`NETRO_SENS_SERIAL` or `NETRO_CTRL_SERIAL`), the test helper generates the reference from the template by performing an internal token substitution (no external script). Common dummy tokens such as `DUMMY_SERIAL`, `000000000000`, `SENSOR_SERIAL` or `CTRL_SERIAL` are replaced by the provided serial.
    - If the template contains no serials (pure fixtures), it will be copied to create the reference (`copy_if_template=True`).
  - If neither reference nor template is available (or a required env var is unset), the fixture calls `pytest.skip()` so the integration test is skipped cleanly.

> Note: `generate_reference.py` is no longer used and has been removed — the generation is handled internally by `tests/conftest.py`.

Environment variables used by fixtures:
- `NETRO_SENS_SERIAL` — sensor serial used to generate sensor reference
- `NETRO_CTRL_SERIAL` — controller serial used to generate controller reference

Fixtures used in tests (examples):
- `need_sensor_reference` — ensures `sensor_response.json`
- `need_controller_reference` — ensures `sprite_response.json`
- `need_sensor_data_reference` — ensures `sensor_response_data.json`
- `need_schedules_reference`, `need_moistures_reference`, `need_events_reference` — ensure other refs (copy from templates if necessary)

### .env.example and local .env

A `.env.example` file (if present) documents the environment variables the tests may require. To provide values locally, copy it to `.env` and edit the values:

```bash
cp .env.example .env
# then open .env and fill NETRO_SENS_SERIAL / NETRO_CTRL_SERIAL etc.
```

Notes:
- `tests/conftest.py` attempts to load a `.env` file automatically (using `python-dotenv` if installed, otherwise a fallback). This allows running integration tests without exporting variables manually.
- Do NOT commit your `.env` containing real serials or secrets. `.env` is ignored by the repo (`.gitignore`) by default.
- In CI, either install `python-dotenv` or provide the required variables as repository Actions secrets / environment variables.

## Security & gitignore

- By default all `.json` files are ignored and only `*_template.json` are tracked. Keep real reference files out of the repository.
- If a sensitive `.json` is already tracked, remove it from the index without deleting local copy:

```bash
git rm --cached path/to/file.json
```

## Troubleshooting

- ImportError in CI for `dotenv`: ensure `python-dotenv` is installed in the job or make import optional in `tests/conftest.py`.
- If integration tests are skipped, confirm `NETRO_SENS_SERIAL` and `NETRO_CTRL_SERIAL` are set or that reference templates exist.

## Contributing

- Add templates (`*_template.json`) for any reference data you add.
- Do not commit files containing real serials or private tokens.

For more details about tests and reference management see `tests/conftest.py` and the test files under `tests/`.
