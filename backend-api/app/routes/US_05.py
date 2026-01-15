"""
US-05: Basic API Health Endpoints
"""
from flask import jsonify

def register(app, session):
    """
    Registers the basic health routes for US-05.
    """
    
    @app.route('/')
    def index():
        return "API is running"

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})