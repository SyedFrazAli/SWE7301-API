
from flask import jsonify

def register(app, session=None):

    @app.route('/')
    def index():
        return "API is running"

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})