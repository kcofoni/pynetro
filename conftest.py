"""Configuration pytest globale pour charger automatiquement les variables d'environnement."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


def pytest_configure(config):  # pylint: disable=unused-argument
    """Configuration automatique de pytest."""
    # Charger le fichier .env s'il existe
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            load_dotenv(env_file)
            print(f"✅ Variables d'environnement chargées depuis {env_file}")
        except ImportError:
            # Fallback : parser manuellement le fichier .env
            _load_env_manually(env_file)
            print(f"✅ Variables d'environnement chargées manuellement depuis {env_file}")


def _load_env_manually(env_file: Path) -> None:
    """Charge manuellement un fichier .env simple (fallback sans python-dotenv)."""
    with env_file.open() as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Gérer les formats: KEY=value et export KEY=value
                if line.startswith('export '):
                    line = line[7:]  # Enlever 'export '

                if '=' in line:
                    key, value = line.split('=', 1)
                    # Enlever les guillemets si présents
                    value = value.strip('"\'')
                    os.environ[key] = value


@pytest.fixture(scope="session", autouse=True)
def load_environment():
    """Fixture pour s'assurer que les variables d'environnement sont chargées."""
    # Cette fixture est automatiquement exécutée au début de chaque session de test
    sens_serial = os.getenv("NETRO_SENS_SERIAL")
    ctrl_serial = os.getenv("NETRO_CTRL_SERIAL")

    if sens_serial and ctrl_serial:
        print(f"🔧 Tests d'intégration activés (SENS: {sens_serial[:4]}..., "
              f"CTRL: {ctrl_serial[:4]}...)")
    else:
        print("⚠️ Tests d'intégration désactivés (variables d'environnement manquantes)")
