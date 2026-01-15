"""
US-13: Authentication and Protected Routes
"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required

def register(app, session):
    """
    Registers the authentication routes for US-13.
    """

    @app.route('/login', methods=['POST'])
    def login():
        try:
            username = request.json.get("username", None)
            password = request.json.get("password", None)
            
            if username != "admin" or password != "password":
                return jsonify({"msg": "Bad username or password"}), 401

            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/protected', methods=['GET'])
    @jwt_required()
    def protected():
        try:
            # Access the identity of the current user with get_jwt_identity
            return jsonify({"msg": "Given valid token, when used, then data returned.", "data": "Top Secret Info"}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
