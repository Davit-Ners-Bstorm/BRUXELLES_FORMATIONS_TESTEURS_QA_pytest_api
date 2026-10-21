from dotenv import load_dotenv
import os
import pytest
import requests

from tests.helpers import login

load_dotenv()

@pytest.fixture(scope="session")
def base_url():
    url = os.getenv("API_URL")
    return url

@pytest.fixture
def real_event(base_url):
    response = requests.get(f"{base_url}/api/events", timeout=5)
    assert response.status_code == 200
    return response.json()[0]

@pytest.fixture(scope='session')
def auth_headers(base_url):
    email = os.getenv('EF_CLIENT_USERNAME')
    password = os.getenv('EF_CLIENT_PASSWORD')
    return login(base_url, email, password)
