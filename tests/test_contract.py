import requests
from jsonschema import validate
from tests.helpers import event_Array_Schema

def test_valide_events_schema(base_url) :
    res = requests.get(base_url+ "/api/events")
    obj = res.json()
    event_list_schema = event_Array_Schema()
    validate(obj, event_list_schema)
