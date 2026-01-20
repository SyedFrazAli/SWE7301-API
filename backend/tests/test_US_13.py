"""
Test suite for US-13: JWT Authentication
Story: As a Product Owner, I want JWT authentication so that only authorised users access data.
DoD: Endpoints require valid JWTs for access.
"""
import pytest
from run import get_app

@pytest.fixture
def client():
    app = get_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_no_token_returns_401(client):
    """
    Checklist: Given no token, when endpoint called, then 401 returned.
    """
    response = client.get('/protected')
    assert response.status_code == 401
    data = response.get_json()
    assert 'msg' in data

def test_invalid_token_access_denied(client):
    """
    Checklist: Given invalid/expired token, when request made, then access denied.
    """
    headers = {'Authorization': 'Bearer invalid_token_here'}
    response = client.get('/protected', headers=headers)
    assert response.status_code == 422  # JWT library returns 422 for invalid tokens
    data = response.get_json()
    assert 'msg' in data

def test_valid_token_returns_data(client):
    """
    Checklist: Given valid token, when used, then data returned.
    """
    # 1st step is to Login to get valid token
    login_response = client.post('/login', json={
        'username': 'admin',
        'password': 'password'
    })
    assert login_response.status_code == 200
    token = login_response.get_json()['access_token']
    
    # 2nd Step is to Use token to access protected endpoint
    headers = {'Authorization': f'Bearer {token}'}
    response = client.get('/protected', headers=headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'msg' in data
    assert 'data' in data
    assert data['data'] == "Top Secret Info"

def test_login_with_wrong_credentials(client):
    """
    Additional test: Login with incorrect credentials should fail.
    """
    response = client.post('/login', json={
        'username': 'wrong',
        'password': 'wrong'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert data['msg'] == "Bad username or password"

def test_login_success(client):
    """
    Additional test: Login with correct credentials should return token.
    """
    response = client.post('/login', json={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
