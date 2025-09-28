# Référence des Réponses API Netro

Ce répertoire contient les structures de réponse de référence pour l'API Netro Public API v1.

## Fichiers de référence

### `sensor_response.json`
Réponse type pour un **sensor/capteur** Netro (ex: capteur d'humidité).

**Structure** :
```json
{
  "status": "OK",
  "meta": { ... },
  "data": {
    "sensor": {
      "name": "Nom du capteur",
            "serial": "34******a4",  // Remplacer par votre numéro de série
      "status": "ONLINE|OFFLINE",
      "version": "3.1",
      "sw_version": "3.1.3", 
      "last_active": "2025-09-28T17:03:26",
      "battery_level": 0.63
    }
  }
}
```

**Champs spécifiques sensor** :
- `battery_level` : Niveau de batterie (0.0 à 1.0)

### `controller_response.json`
Réponse type pour un **controller/contrôleur** Netro (ex: contrôleur d'arrosage).

**Structure** :
```json
{
  "status": "OK", 
  "meta": { ... },
  "data": {
    "device": {
      "name": "Nom du contrôleur",
      "serial": "YYYYYYYYYYYY",  // Remplacer par votre numéro de série
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

**Champs spécifiques controller** :
- `zone_num` : Nombre de zones d'arrosage
- `zones[]` : Liste des zones configurées

## Usage dans les tests

Ces fichiers sont utilisés comme référence pour :
- Valider les structures de réponse dans les tests d'intégration
- Documenter les différences entre sensor et controller
- Créer des mocks réalistes dans les tests unitaires

## Génération

Les fichiers sont générés automatiquement via :
```bash
# Exécuter le script de génération des références
python -c "from tests.generate_references import generate; generate()"
```

Dernière mise à jour : 28 septembre 2025