import pytest
from US_06 import app  # Note: Use an underscore if your filename has a dash or space

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_status_endpoint(client):
    # This test is for a feature that DOES NOT EXIST yet
    response = client.get('/status')
    assert response.status_code == 200
    assert response.get_json() == {"message": "System is online"}