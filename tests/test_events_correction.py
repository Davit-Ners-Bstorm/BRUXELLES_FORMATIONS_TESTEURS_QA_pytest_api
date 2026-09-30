import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

def test_event_published_only():
    response = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT)
    assert response.status_code == 200, response.text

    events = response.json()

    for e in events:
        assert e["status"] == "published"

def test_event_list_not_empty():
    response = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    events = response.json()
    # Verifie si la lsite est vide
    assert len(events) > 0, "Liste vide"

def test_event_structure_ok():
    response = requests.get(f"{BASE_URL}/api/events", timeout=TIMEOUT)
    assert response.status_code == 200, response.text
    events = response.json()
    for e in events:
        assert "id" in e
        assert type(e["id"]) == int
        assert "title" in e
        assert type(e["title"]) == str
        assert "description" in e
        assert type(e["description"]) == str
        assert "city" in e
        assert type(e["city"]) == str
        assert "venue" in e
        assert type(e["venue"]) == str
        assert "starts_at" in e
        assert type(e["starts_at"]) == str
        assert "capacity" in e
        assert type(e["capacity"]) == int
        assert "status" in e
        assert type(e["status"]) == str
        assert "cover_color" in e
        assert type(e["cover_color"]) == str

