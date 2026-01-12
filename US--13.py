from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)


app.config["JWT_SECRET_KEY"] = "super-secret-key-change-me" 
jwt = JWTManager(app)

@app.route('/')
def index():
    return "API is running"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# 1. Login endpoint to get a token
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    
    # Basic check (In reality, check against a database)
    if username != "admin" or password != "password":
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# 2. Protected endpoint (Meets DoD requirements)
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    return jsonify({"msg": "Given valid token, when used, then data returned.", "data": "Top Secret Info"})

if __name__ == '__main__':
    app.run(debug=True)