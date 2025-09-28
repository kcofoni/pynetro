# pynetro

Async Python wrapper for Netro API — HTTP-agnostic (works with adapters).
Designed to integrate with Home Assistant but usable anywhere.

## Installation

### 🚀 Installation rapide

```bash
# Cloner le projet
git clone https://github.com/kcofoni/pynetro.git
cd pynetro

# Installer en mode développement
pip install -e .
```

### 🛠️ Installation complète pour le développement

#### 1. Prérequis
- Python 3.10 ou supérieur
- git

#### 2. Configuration de l'environnement

```bash
# Cloner le projet
git clone https://github.com/kcofoni/pynetro.git
cd pynetro

# Créer un environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Sur Linux/macOS :
source .venv/bin/activate

# Sur Windows :
# .venv\Scripts\activate

# Vérifier que l'environnement est activé (le prompt doit afficher (.venv))
which python  # Doit pointer vers .venv/bin/python
```

#### 3. Installation des dépendances

```bash
# Installer le projet en mode développement
pip install -e .

# Installer les dépendances de développement (tests, linting, etc.)
pip install -r requirements-dev.txt
```

#### 4. Vérification de l'installation

```bash
# Vérifier que tout fonctionne
pytest tests/test_client.py -v

# Vérifier le linting
ruff check src/ tests/
```

#### 5. Configuration pour les tests d'intégration (optionnel)

```bash
# Créer un fichier .env avec vos numéros de série d'appareils Netro
cp .env.example .env
# Puis éditer .env avec vos vraies valeurs

# Tester les intégrations (nécessite une connexion internet et des appareils Netro)
pytest tests/test_integration.py -v -m integration
```

### 🔧 Résolution de problèmes courants

#### Environnement virtuel non activé
```bash
# Vérifier que l'environnement est activé
which python  # Doit pointer vers .venv/bin/python
echo $VIRTUAL_ENV  # Doit afficher le chemin vers .venv

# Si pas activé :
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

#### Erreurs d'import lors des tests
```bash
# Réinstaller le projet en mode développement
pip install -e .
```

#### Tests d'intégration skippés
```bash
# Les tests d'intégration nécessitent des variables d'environnement
export NETRO_SENS_SERIAL="votre_serial_sensor"
export NETRO_CTRL_SERIAL="votre_serial_controller"

# Vérifier que les variables sont définies
echo $NETRO_SENS_SERIAL $NETRO_CTRL_SERIAL
```

### Tests

Le projet dispose d'une suite de tests complète avec 14 tests (5 unitaires + 9 intégration).

```bash
# Lancer tous les tests
pytest tests/ -v

# Tests unitaires seulement (toujours disponibles)
pytest tests/test_client.py -v

# Tests d'intégration (nécessitent des variables d'environnement)
pytest tests/test_integration.py -v -m integration
```

📖 **Documentation complète des tests** : Voir [`tests/README.md`](tests/README.md) pour toutes les commandes et options avancées.
