# J4 — Suite de tests API EventFlow avec PyTest

Ce dossier est **votre** projet de tests. Il est volontairement presque vide : vous allez le construire pendant la journée.

## Contenu de départ

```text
j4-api-pytest/
    README.md
    requirements.txt       pytest, requests, jsonschema
    pytest.ini             configuration PyTest
    scripts/
        explorer_catalogue.py   script d'exploration « façon J2 » (point de départ)
    tests/                 vide : vos tests iront ici
    schemas/               vide : vos schémas JSON (exercice 4)
    data/                  vide : vos jeux de données de test (exercice 6)
```

## Installation

EventFlow doit tourner (API sur `http://localhost:8000`).

```bash
# depuis le dossier j4-api-pytest
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Vérifier que tout est prêt

```bash
curl http://localhost:8000/api/health
```

Doit répondre `{"status":"ok","service":"eventflow-api"}`. La documentation interactive de l'API est sur `http://localhost:8000/docs`.

```bash
python scripts/explorer_catalogue.py
pytest
```

Au départ, `pytest` répond `no tests ran` : c'est normal, le dossier `tests/` est vide.

## Viser une autre API

À partir de l'exercice 3, l'URL de l'API sera lue dans la variable d'environnement `API_URL` :

```bash
# Windows (PowerShell)
$env:API_URL = "http://localhost:8000"
# macOS / Linux
export API_URL=http://localhost:8000
```

Sans variable, la valeur par défaut `http://localhost:8000` s'applique.
