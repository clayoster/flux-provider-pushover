import pytest
import os

# Set Environment Variables
os.environ["PUSHOVER_USER_KEY"] = "test_user_key"
os.environ["PUSHOVER_API_TOKEN"] = "test_api_token"

from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()
