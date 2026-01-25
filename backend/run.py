from flask import Flask, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.db import engine, SessionLocal, Base
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

def get_app():
    app = Flask(__name__)
    CORS(app)

    # JWT Config
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-flask-key")  # Required for Authlib/Session
    JWTManager(app)

    # Security: Talisman (Headers + CSP)
    # Force HTTPS only if NOT in debug mode (Production)
    csp = {
        'default-src': '\'self\'',
        'img-src': '*',
        'script-src': ['\'self\'', '\'unsafe-inline\'', '\'unsafe-eval\'', 'https://cdnjs.cloudflare.com'], # unsafe-inline/eval often needed for Swagger/React dev
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'https://fonts.googleapis.com', 'https://cdnjs.cloudflare.com'],
        'font-src': ['\'self\'', 'https://fonts.gstatic.com', 'data:']
    }
    
    # production: FLASK_ENV=production OR (debug=False AND testing=False AND FLASK_TESTING!=True)
    # We want HTTPS in production, but NOT in local debug OR test runs.
    is_testing = app.testing or os.getenv('FLASK_TESTING') == 'True'
    is_production = os.getenv('FLASK_ENV') == 'production' or (not app.debug and not is_testing)
    
    Talisman(app, 
             content_security_policy=csp, 
             force_https=is_production)

    # Security: Limiter (Rate Limiting)
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )

    # Swagger Documentation
    Swagger(app)

    # Import models to register with SQLAlchemy
    from app.routes.observation import ObservationRecord, Product, Subscription

    # Initialize DB tables
    Base.metadata.create_all(bind=engine)

    # Seed initial products if none exist
    db = SessionLocal()
    if db.query(Product).count() == 0:
        products = [
            Product(id=1, name="Crop Health Monitoring", description="High-res spectral analysis for agriculture.", price="$499/mo"),
            Product(id=2, name="Wildfire Risk Assessment", description="Real-time thermal imaging and risk modeling.", price="$799/mo"),
            Product(id=3, name="Urban Expansion Tracking", description="Monthly change detection for city planning.", price="$299/mo"),
            Product(id=4, name="Deforestation Alert System", description="Instant notification of illegal logging activities.", price="$599/mo")
        ]
        db.add_all(products)
        db.commit()

        # Seed Observations
        observations = [
            ObservationRecord(product_id=1, satellite_id="SENTINEL-2", notes="Healthy wheat field analysis", coordinates="34.05, -118.24"),
            ObservationRecord(product_id=2, satellite_id="LANDSAT-8", notes="Thermal anomaly detected in forest", coordinates="45.52, -122.67"),
            ObservationRecord(product_id=3, satellite_id="SPOT-7", notes="New construction area identified", coordinates="51.50, -0.12"),
            ObservationRecord(product_id=4, satellite_id="SENTINEL-1", notes="Logging tracks spotted", coordinates="-3.46, -62.21")
        ]
        db.add_all(observations)
        
        # Seed Subscriptions
        # full_user: all subscriptions
        for pid in [1, 2, 3, 4]:
            db.add(Subscription(user_id="full_user", product_id=pid))
        
        # partial_user: products 1 and 2
        for pid in [1, 2]:
            db.add(Subscription(user_id="partial_user", product_id=pid))
        
        # none_user: no subscriptions
        
        db.commit()
    db.close()

    # Create a per-request session
    @app.before_request
    def create_session():
        g.db = SessionLocal()

    @app.teardown_appcontext
    def remove_session(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    # Import and register routes
    import app.routes.observation as observation
    import app.routes.filtering as filtering
    import app.routes.healthApi as healthApi
    import app.models.jwtAuth as jwtAuth

    # Register routes without passing a long-lived session
    observation.register(app)
    filtering.register(app)
    healthApi.register(app)
    jwtAuth.register(app)

    return app


if __name__ == "__main__":
    app = get_app()
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)
