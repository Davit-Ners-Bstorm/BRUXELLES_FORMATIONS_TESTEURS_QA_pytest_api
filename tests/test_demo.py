# Remise à niveau
from typing import Literal

import requests
import pytest
# from tests.helpers import TIMEOUT

TIMEOUT = 5

BASE_URL = "http://localhost:8000"

# result = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT)
# events: list[dict] = result.json()

# print(events)

# for event in events:
#     print(event["title"])

# def lamda_fct(e):
#     return e["title"]


# print([*map(lambda e: e["title"], events)])

# def fct(event):
#     return event["id"]

# events.sort(reverse=True, key=lambda event: event["id"])

# events.sort(key=lambda event: event["title"])

# print(events)

params = {
    "city": "Bruxelles",
    "q": "atelier"
}

result = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT, params=params)
events_in_bruxelles: list[dict] = result.json()

# print(events_in_bruxelles)

# @pytest.mark.skip
@pytest.mark.xfail
def test_get_all_events():
    response = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    events = response.json()
    assert len(events) > 0

def test_echouaayyy():
    response = requests.get(f"{BASE_URL}/api/events/999", timeout=TIMEOUT)
    assert response.status_code == 404, response.text

@pytest.mark.parametrize("id", [
    pytest.param(999, marks=pytest.mark.xfail), # => Même que les autres cas de test en bas, mais celui la permet de rajouter un marqueur sur le test case
    (42),
    (-1),
    (-99),
    (0)
], ids=["CAS_999", "CAS_42", "CAS_-1", "CAS_-99", "CAS_0"])
def test_event_404(id: Literal[999] | Literal[42] | Literal[-1] | Literal[-99] | Literal[0], base_url: str | None):
    response = requests.get(f"{base_url}/api/events/{id}", timeout=TIMEOUT)
    assert response.status_code == 404, response.text



response = requests.get(f"{BASE_URL}/api/events/1.5", timeout=TIMEOUT)
print(response.status_code, response.json())



ADRESSE_SHEMA = {
    "type": "object",
    "required": ["rue", "code_postal", "numero"],
    "properties": {
        "rue": {"type": "string"},
        "code_postal": {"type": "string"},
        "numero": {"type": "integer"},
    }
}

EVENT_SHEMA = {
    "type": "object",
    "required": ["id", "title", "city"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "integer", "minimum": 0},
        "title": {"type": "string", "minLength": 3},
        "city": {"type": "string"},
        "capacity": {"type": "integer", "minimum": 0},
        "adresse": ADRESSE_SHEMA,
        "status": {"type": "string", "enum": ["published", "finished", "blocked"]}
    }
}

EVENTS_SHEMA = {
    "type": "array",
    "items": EVENT_SHEMA,
    "minItems": 1
}

from jsonschema import validate, ValidationError

def test_shema_event():
    event_shema_test = {
        "id": 1,
        "title": "Concert de Rock Davit Until They Fall - Djyn",
        "city": "Braine L'Alleud",
        "status": "blocked"
    }

    validate(event_shema_test, EVENT_SHEMA)

from tests.helpers import load_json

IMPORTED_SCHEMA = load_json("schemas/event_schema.json")

def test_shema_imported_event():
    event_test = {
        "id": 5,
        "title": "test",
        "city": "test"
    }

    validate(event_test, IMPORTED_SCHEMA)


def test_shema_doit_casser():
    event_test = {
        "id": 5,
        "title": "test",
        "city": "test"
    }

    del event_test["id"]

    with pytest.raises(ValidationError):
        validate(event_test, IMPORTED_SCHEMA)




