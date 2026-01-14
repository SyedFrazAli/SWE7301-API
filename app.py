import os
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Standard SQLite URL - Works on all machines
DATABASE_URL = "sqlite:///app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_app():
    app = Flask(__name__)
    
    # We create a scoped session for the routes
    session = SessionLocal()
    import US_07
    import US_08
    import US_12
    
    # Registration is critical for the routes to exist
    US_07.register(app, session)
    US_08.register(app, session)
    US_12.register(app, session)

    return app

if __name__ == '__main__':
    app = get_app()
    print("Server running on http://127.0.0.1:5000")
    app.run(debug=True)