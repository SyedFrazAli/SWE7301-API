from flask import Flask, g
from flask_jwt_extended import JWTManager
from app.db import engine, SessionLocal, Base
import os

def get_app():
    app = Flask(__name__)

    # JWT Config
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    JWTManager(app)

    # Import models to register with SQLAlchemy
    from app.routes.observation import ObservationRecord

    # Initialize DB tables
    Base.metadata.create_all(bind=engine)

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
