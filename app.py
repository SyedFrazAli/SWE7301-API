import os
from flask import Flask
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Standard SQLite URL - Works on all machines
DATABASE_URL = "sqlite:///app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_app():
    app = Flask(__name__)
    
    # JWT Configuration for US-13 (Authentication)
    app.config["JWT_SECRET_KEY"] = "super-secret-key-change-me"
    jwt = JWTManager(app)
    
    # We create a scoped session for the routes
    session = SessionLocal()
    import US_10
    import US_09
    import US_06
    import US_13
    
    # Registration is critical for the routes to exist
    US_10.register(app, session)
    US_09.register(app, session)
    US_06.register(app, session)
    US_13.register(app, session)

    return app

if __name__ == '__main__':
    app = get_app()
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)