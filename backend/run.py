import os
from flask import Flask
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Standard SQLite URL - Works on all machines
DATABASE_URL = "sqlite:///run.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_app():
    app = Flask(__name__)

    app.config["JWT_SECRET_KEY"] = "super-secret-key-change-me"
    JWTManager(app)

    session = SessionLocal()

    import app.routes.observation as observation
    import app.routes.filtering as filtering
    import app.routes.healthApi as healthApi
    import app.models.jwtAuth as jwtAuth
    from app.db import Base

    Base.metadata.create_all(bind=engine)

    observation.register(app, session)
    filtering.register(app, session)
    healthApi.register(app, session)
    jwtAuth.register(app, session)

    return app


if __name__ == '__main__':
    app = get_app()
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)
