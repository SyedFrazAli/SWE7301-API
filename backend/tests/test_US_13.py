"""
Test suite for US-13: JWT Authentication
Story: As a Product Owner, I want JWT authentication so that only authorised users access data.
DoD: Endpoints require valid JWTs for access.
"""
import pytest
from run import get_app
from app.db import engine, SessionLocal
from app.routes.observation import User
from werkzeug.security import generate_password_hash
from datetime import datetime

import os

@pytest.fixture
def client():
    os.environ['FLASK_TESTING'] = 'True'
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

@pytest.fixture
def db_session():
    session = SessionLocal()
    yield session
    session.close()

def test_valid_token_returns_data(client, db_session):
    """
    Checklist: Given valid token, when used, then data returned.
    """
    # 0. Setup: Create User
    email = "admin@test.com"
    password = "password"
    
    # Clean up if exists
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()
        
    user = User(
        email=email,
        password=generate_password_hash(password),
        first_name="Admin",
        last_name="User",
        is_verified=1
    )
    db_session.add(user)
    db_session.commit()

    # 1. Login to trigger OTP
    login_response = client.post('/login', json={
        'email': email,
        'password': password
    })
    assert login_response.status_code == 200
    json_data = login_response.get_json()
    assert json_data.get('otp_required') is True
    
    # 2. Get OTP from DB (Simpler than file for unit tests)
    db_session.refresh(user)
    otp = user.otp_code
    assert otp is not None
    
    # 3. Verify OTP to get Token
    verify_response = client.post('/verify-login-otp', json={
        'email': email,
        'otp': otp
    })
    assert verify_response.status_code == 200
    token = verify_response.get_json()['access_token']
    
    # 4. Use token to access protected endpoint
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
        'email': 'wrong@test.com',
        'password': 'wrong'
    })
    assert response.status_code == 401
    data = response.get_json()
    assert data['msg'] == "Bad email or password"

def test_login_success(client, db_session):
    """
    Additional test: Login with correct credentials should return OTP requirement.
    """
    # Setup User
    email = "login_test@example.com"
    password = "password"
    
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    user = User(
        email=email,
        password=generate_password_hash(password),
        first_name="Login",
        last_name="Test",
        is_verified=1
    )
    db_session.add(user)
    db_session.commit()

    response = client.post('/login', json={
        'email': email,
        'password': password
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('otp_required') is True
    assert 'otp_required' in data
