TIMEOUT = 5
import json
import pytest
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_json(relative_path):
    with open(PROJECT_ROOT / relative_path, encoding="utf-8") as f:
        return json.load(f)

def event_Array_Schema() : 
    eventOut = load_json("schemas/eventOut.json")
    return {
        "type" : "array",
        "items" : eventOut
    }
def login(base_url, email,password):
    response = requests.post(f'{base_url}/api/auth/token', data={'username':email, 'password':password},timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    login_cred = response.json()
    return {
        'Authorization' : f"{login_cred["token_type"].capitalize()} {login_cred['access_token']}" 
    }

def get_all_events(base_url):
    response = requests.get(f"{base_url}/api/events", timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    return response.json()

def get_bookable_event_cat(base_url, events_summary, min_available = 1):
    for event in events_summary:
        response = requests.get(f"{base_url}/api/events/{event["id"]}", timeout=TIMEOUT)
        assert response.status_code == 200, response.text
        detail_event = response.json()
        if detail_event["status"] != 'published':
            continue
        for categorie in detail_event["categories"]:
            if categorie["available"] >= min_available:
                return {
                    "event" : event, 
                    "categorie" : categorie
                }
    return None

        
