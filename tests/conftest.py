from dotenv import load_dotenv
import os
import pytest

load_dotenv()

@pytest.fixture(scope="session")
def base_url():
    url = os.getenv("API_URL")
    return url
