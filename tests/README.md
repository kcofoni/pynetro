# Tests pour PyNetro

Ce dossier contient la suite de tests complète pour PyNetro avec 14 tests (5 unitaires + 9 intégration).

## 🔒 Sécurité

⚠️ **Important** : Les tests d'intégration utilisent des variables d'environnement pour protéger les données sensibles (numéros de série des appareils).

### Variables d'environnement requises

#### Méthode 1 : Fichier .env (recommandée)

Créez un fichier `.env` à la racine du projet :

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos vraies valeurs
# .env
export NETRO_SENS_SERIAL=votre_numero_serie_sensor  
export NETRO_CTRL_SERIAL=votre_numero_serie_controller
```

Les tests chargeront automatiquement ce fichier ! ✨

#### Méthode 2 : Variables d'environnement manuelles

```bash
export NETRO_SENS_SERIAL="votre_numero_serie_sensor"
export NETRO_CTRL_SERIAL="votre_numero_serie_controller"
```

## 🧪 Lancer tous les tests

```bash
# Tous les tests (unitaires + intégration si variables définies)
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=pynetro --cov-report=html

# Avec temps d'exécution détaillé
pytest tests/ -v --durations=10
```

## 🔬 Tests unitaires (toujours disponibles)

```bash
# Tous les tests unitaires
pytest tests/test_client.py -v

# Test unitaire spécifique
pytest tests/test_client.py::TestNetroClient::test_get_info_success -v

# Tests unitaires avec couverture
pytest tests/test_client.py --cov=pynetro
```

## 🌐 Tests d'intégration (nécessitent les variables d'environnement)

```bash
# 1. Définir les variables d'environnement
export NETRO_SENS_SERIAL="votre_numero_serie_sensor"
export NETRO_CTRL_SERIAL="votre_numero_serie_controller"

# 2. Lancer tous les tests d'intégration
pytest tests/test_integration.py -v -m integration

# 3. Test d'intégration spécifique
pytest tests/test_integration.py::TestNetroClientIntegration::test_get_info_sensor_device -v

# 4. Voir les tests qui seraient skippés (mode sécurisé)
pytest tests/test_integration.py -v -rs
```

## 🎯 Tests sélectifs

```bash
# Seulement les tests unitaires
pytest -m "not integration" -v

# Seulement les tests d'intégration
pytest -m integration -v

# Tests par motif (exemple : tous les tests get_info)
pytest tests/ -k "test_get_info" -v

# Test unique par son nom complet
pytest tests/test_client.py::TestNetroClient::test_get_info_success -v
```

## � Couverture de code

### Commandes de base

```bash
# Couverture des tests unitaires
pytest tests/test_client.py --cov=pynetro

# Couverture de tous les tests
pytest tests/ --cov=pynetro

# Avec rapport détaillé des lignes manquantes
pytest tests/ --cov=pynetro --cov-report=term-missing
```

### Rapports HTML interactifs

```bash
# Générer un rapport HTML détaillé
pytest tests/ --cov=pynetro --cov-report=html

# Le rapport sera dans htmlcov/index.html
# Ouvrir avec: firefox htmlcov/index.html (ou votre navigateur)
```

### Options avancées de couverture

```bash
# Échouer si couverture < 80%
pytest tests/ --cov=pynetro --cov-fail-under=80

# Couverture avec exclusion de fichiers
pytest tests/ --cov=pynetro --cov-report=html --cov-report=term

# Couverture seulement des nouveaux fichiers modifiés
pytest tests/ --cov=pynetro --cov-report=term --cov-branch
```

### Interprétation des résultats

```
Name                      Stmts   Miss  Cover
---------------------------------------------
src/pynetro/__init__.py       3      0   100%  ✅ Parfait
src/pynetro/client.py       181    117    35%  ⚠️ Besoin de plus de tests
src/pynetro/http.py          16      0   100%  ✅ Parfait
---------------------------------------------
TOTAL                       200    117    42%  🎯 Objectif: >80%
```

- **Stmts** : Nombre total de lignes de code
- **Miss** : Lignes non couvertes par les tests
- **Cover** : Pourcentage de couverture

## �🔍 Options avancées

```bash
# Mode verbose avec traceback court
pytest tests/ -v --tb=short

# Arrêter au premier échec
pytest tests/ -x

# Variables d'environnement en une ligne
NETRO_SENS_SERIAL="sensor_serial" NETRO_CTRL_SERIAL="ctrl_serial" pytest tests/ -v

# Mode parallèle (nécessite: pip install pytest-xdist)
pytest tests/ -v -n auto

# Profiling des tests les plus lents
pytest tests/ --durations=10
```

## 📁 Structure des tests

```
tests/
├── __init__.py                    # Package Python pour les tests
├── README.md                      # Ce fichier - Documentation des tests
├── pytest.ini                    # Configuration pytest (à la racine)
├── test_client.py                 # Tests unitaires (5 tests)
├── test_integration.py            # Tests d'intégration (9 tests)
├── aiohttp_client.py             # Client HTTP réel pour les tests d'intégration
├── generate_references.py        # Script de génération des fichiers de référence
└── reference_data/
    ├── .gitignore                # Ignore les fichiers JSON sensibles
    └── README.md                 # Documentation des structures API
```

## 🚀 Génération des fichiers de référence

Pour générer les structures de référence de l'API :

```bash
# 1. Définir les variables d'environnement
export NETRO_SENS_SERIAL="votre_numero_serie_sensor"
export NETRO_CTRL_SERIAL="votre_numero_serie_controller"

# 2. Générer les références
python tests/generate_references.py
```

**Note** : Les fichiers générés contiennent des données sensibles et ne doivent pas être commitées dans Git (protégés par `.gitignore`).

## 🛠️ Développement des tests

### Ajout d'un nouveau test unitaire
1. Ouvrir `tests/test_client.py`
2. Ajouter votre test dans la classe `TestNetroClient`
3. Utiliser les mocks `MockHTTPClient` et `MockHTTPResponse`

### Ajout d'un nouveau test d'intégration
1. Ouvrir `tests/test_integration.py`
2. Ajouter le décorateur `@skip_if_no_serials` si besoin des variables d'env
3. Utiliser `AiohttpClient` pour les appels HTTP réels
4. Marquer avec `@pytest.mark.integration`

### Bonnes pratiques
- ✅ Tests unitaires : Pas de dépendances externes, utiliser les mocks
- ✅ Tests d'intégration : Variables d'environnement, marqueur `integration`
- ✅ Noms explicites : `test_get_info_success`, `test_get_info_api_error`
- ✅ Documentation : Docstrings en français pour les tests complexes

## 🚨 Dépannage

### Erreur "pytest-cov not found"
```bash
# Installer pytest-cov
pip install pytest-cov

# Ou réinstaller toutes les dépendances de dev
pip install -r requirements-dev.txt
```

### Couverture à 0% ou incorrecte
```bash
# Vérifier que le package est installé en mode développement
pip install -e .

# Vérifier le chemin des sources
pytest tests/ --cov=src/pynetro --cov-report=term
```

### Tests d'intégration qui ne se lancent pas
```bash
# Vérifier les variables d'environnement
echo $NETRO_SENS_SERIAL $NETRO_CTRL_SERIAL

# Ou vérifier le fichier .env
cat .env

# Créer le fichier .env si absent
cp .env.example .env
```

### Erreurs d'import
```bash
# Réinstaller le projet
pip install -e .

# Vérifier la structure des packages
python -c "import pynetro; print(pynetro.__file__)"
```