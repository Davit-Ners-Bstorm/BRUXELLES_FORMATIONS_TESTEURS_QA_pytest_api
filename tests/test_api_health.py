import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 5

def test_healh_respond_ok():
    response = requests.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["status"] == "ok"
