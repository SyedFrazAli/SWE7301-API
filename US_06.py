from flask import Flask, jsonify
from flasgger import Swagger
app = Flask(__name__)
swagger= Swagger(app)

@app.route('/')
def index():
     
    return "API is running on swagger"

@app.route('/status')
def status():
    return jsonify({"message": "System is online"})
@app.route('/health')
def health():

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)