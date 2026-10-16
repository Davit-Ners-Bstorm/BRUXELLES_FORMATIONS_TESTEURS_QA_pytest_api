# Remise à niveau
import requests
import pytest

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

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
def test_event_404(id):
    response = requests.get(f"{BASE_URL}/api/events/{id}", timeout=TIMEOUT)
    assert response.status_code == 404, response.text



response = requests.get(f"{BASE_URL}/api/events/1.5", timeout=TIMEOUT)
print(response.status_code, response.json())
