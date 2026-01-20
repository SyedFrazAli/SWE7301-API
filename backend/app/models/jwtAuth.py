"""
US-13: Authentication and Protected Routes
"""
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

def register(app):
    """
    Registers login and protected routes with JWT authentication.
    """

    @app.route('/login', methods=['POST'])
    def login():
        try:
            username = request.json.get("username")
            password = request.json.get("password")
            
            # Simple hardcoded authentication for demo
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
            current_user = get_jwt_identity()  # get the identity from the JWT
            return jsonify({
                "msg": "Given valid token, when used, then data returned.",
                "user": current_user,
                "data": "Top Secret Info"
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
