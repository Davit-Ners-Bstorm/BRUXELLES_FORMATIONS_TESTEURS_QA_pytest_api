import pytest
import requests
from jsonschema import validate,ValidationError
from tests.helpers import event_Array_Schema , load_json

def test_valide_events_schema(base_url) :
    res = requests.get(base_url+ "/api/events")
    obj = res.json()
    event_list_schema = event_Array_Schema()
    validate(obj, event_list_schema)

def test_echou_events_schema(base_url):
    res = requests.get(base_url+ "/api/events")
    obj = res.json()
    event = obj[0]
    schema = load_json("schemas/eventOut.json")
    del event["id"]
    with pytest.raises(ValidationError):
        validate(event,schema)

@pytest.mark.parametrize("key, wrong_value", [
    ("capacity", "more"),
    ("capacity", -5),
    ("capacity", 1.24),
    ("id", -5)
], ids= ["Must be a valid value", "Value must be a string", "Value must be an integer", "Id must be positive"])

def test_broken_value(real_event, key, wrong_value):
    mock_event = dict(real_event)
    mock_event[key] = wrong_value
    schema = load_json("schemas/eventOut.json")

    with pytest.raises(ValidationError):
        validate(instance=mock_event, schema=schema)

   





