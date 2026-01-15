import pytest
from flask import Flask
from US_06 import register

@pytest.fixture
def client():
    # Create a test Flask app
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Register US_06 routes (session not needed for these routes)
    register(app, None)
    
    with app.test_client() as client:
        yield client

def test_status_endpoint(client):
    response = client.get('/status')
    assert response.status_code == 200
    assert response.get_json() == {"message": "System is online"}

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.data.decode() == "API is running on swagger"