from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "API is running"

# ADD THIS SECTION TO MEET TRELLO REQUIREMENTS
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True)