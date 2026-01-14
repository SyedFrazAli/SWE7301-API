from flask import request, jsonify

def register(app, session=None):
    """
    Registers standard JSON response patterns.
    """

    # Health check endpoint
    @app.route("/api/status", methods=["GET"])
    def get_status():
        return jsonify({
            "status": "running",
            "message": "Orders API is operational"
        }), 200

    # Error handlers to ensure all errors return JSON
    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "error": "Bad Request",
            "message": "Invalid order data provided.",
            "code": 400
        }), 400

    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({
            "error": "Not Found",
            "message": "Order not found.",
            "code": 404
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "error": "Method Not Allowed",
            "message": "This HTTP method is not supported for this endpoint.",
            "code": 405
        }), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error": "Internal Server Error",
            "message": "Failed to process order request.",
            "code": 500
        }), 500