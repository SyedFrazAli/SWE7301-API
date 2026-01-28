"""
Shared pytest fixtures and utilities for all test modules.
Provides isolated test database, authenticated clients, and mock utilities.
"""
import pytest
import os
import tempfile
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token

from run import get_app
from app.db import Base, engine, SessionLocal
from app.routes.observation import User, Product, Subscription, ObservationRecord


@pytest.fixture(scope='function')
def app():
    """Create and configure a test Flask application with isolated database."""
    # Set testing environment
    os.environ['FLASK_TESTING'] = 'True'
    os.environ['FLASK_ENV'] = 'testing'
    
    # Create test app
    test_app = get_app()
    test_app.config['TESTING'] = True
    test_app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # Create all tables for testing
    Base.metadata.create_all(engine)
    
    yield test_app
    
    # Cleanup: drop all tables after test
    Base.metadata.drop_all(engine)


@pytest.fixture(scope='function')
def client(app):
    """Provide a Flask test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def db_session():
    """Provide a database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope='function')
def test_user(db_session):
    """Create a verified test user."""
    email = "testuser@example.com"
    password = "TestPassword123"
    
    # Clean up if exists
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()
    
    user = User(
        email=email,
        password=generate_password_hash(password),
        first_name="Test",
        last_name="User",
        is_verified=1,
        is_2fa_enabled=0
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return {
        'user': user,
        'email': email,
        'password': password
    }


@pytest.fixture(scope='function')
def auth_headers(app, test_user):
    """Generate authentication headers with valid JWT token."""
    with app.app_context():
        access_token = create_access_token(identity=test_user['email'])
    return {'Authorization': f'Bearer {access_token}'}


@pytest.fixture(scope='function')
def test_products(db_session):
    """Create test products in the database."""
    # Check if products already exist (from seed data)
    existing_products = db_session.query(Product).all()
    if existing_products:
        return existing_products
    
    # Create test products if they don't exist
    products = [
        Product(id=1, name="Crop Health Monitoring", description="Test product 1", 
                price="$499/mo", stripe_price_id="price_test_crop"),
        Product(id=2, name="Wildfire Risk Assessment", description="Test product 2", 
                price="$399/mo", stripe_price_id="price_test_wildfire"),
        Product(id=3, name="Urban Expansion Tracking", description="Test product 3", 
                price="$299/mo", stripe_price_id="price_test_urban"),
        Product(id=4, name="Deforestation Alert System", description="Test product 4", 
                price="$199/mo", stripe_price_id="price_test_deforest"),
        Product(id=5, name="Pro Plan (All Access)", description="Full access", 
                price="$999/mo", stripe_price_id="price_test_pro")
    ]
    
    for product in products:
        db_session.merge(product)  # Use merge to handle existing IDs
    db_session.commit()
    
    return db_session.query(Product).all()


@pytest.fixture(scope='function')
def test_subscription(db_session, test_user, test_products):
    """Create a test subscription for the test user to product 1."""
    subscription = Subscription(
        user_id=test_user['email'],
        product_id=1
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription


@pytest.fixture(scope='function')
def test_observation(db_session, test_products):
    """Create a test observation record."""
    obs = ObservationRecord(
        product_id=1,
        satellite_id="TEST-SAT-1",
        coordinates="40.7128, -74.0060",
        value="0.75",
        unit="NDVI",
        confidence=95.5,
        notes="Test observation",
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)
    return obs


@pytest.fixture
def mock_stripe_checkout_session():
    """Mock Stripe checkout session data."""
    return {
        'id': 'cs_test_123456',
        'url': 'https://checkout.stripe.com/test',
        'payment_status': 'paid',
        'metadata': {
            'product_id': '1',
            'user_email': 'testuser@example.com'
        }
    }


@pytest.fixture
def mock_stripe_webhook_event():
    """Mock Stripe webhook event data."""
    return {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_webhook',
                'payment_status': 'paid',
                'metadata': {
                    'product_id': '2',
                    'user_email': 'webhook@example.com'
                }
            }
        }
    }


@pytest.fixture
def mock_email_send(mocker):
    """Mock email sending function to avoid actual email delivery."""
    return mocker.patch('app.models.jwtAuth.send_email_otp', return_value=True)
