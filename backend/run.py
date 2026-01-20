from flask import Flask, g
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from app.db import engine, SessionLocal, Base
import os

def get_app():
    app = Flask(__name__)
    CORS(app)

    # JWT Config
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    JWTManager(app)

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
            Product(name="Crop Health Monitoring", description="High-res spectral analysis for agriculture.", price="$499/mo"),
            Product(name="Wildfire Risk Assessment", description="Real-time thermal imaging and risk modeling.", price="$799/mo"),
            Product(name="Urban Expansion Tracking", description="Monthly change detection for city planning.", price="$299/mo"),
            Product(name="Deforestation Alert System", description="Instant notification of illegal logging activities.", price="$599/mo")
        ]
        db.add_all(products)
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
