from flask import request, jsonify

def register(app, session=None):
    """
    Registers GeoScope Analytics API endpoints and standardizes JSON responses.
    This fulfills User Story US-07 regarding HTTP method support.
    """

    # API ENDPOINTS 

    @app.route("/api/v1/insights", methods=["GET", "POST"])
    def manage_insights():
        if request.method == "GET":
            # Logic to retrieve satellite insights 
            return jsonify({
                "source": "GeoScope fleet",
                "data": [
                    {"id": "SAT-01", "type": "wildfire_risk", "status": "low"},
                    {"id": "SAT-02", "type": "deforestation", "status": "alert"}
                ]
            }), 200
        
        elif request.method == "POST":
            # Logic to create a new on-demand imagery request 
            data = request.get_json()
            return jsonify({
                "message": "Satellite tasking request created.",
                "request_id": "GEO-9982",
                "received_data": data
            }), 201

    @app.route("/api/v1/insights/<int:insight_id>", methods=["PUT", "PATCH", "DELETE"])
    def modify_insight(insight_id):
        if request.method == "PUT":
            # Fully replace an existing insight record
            return jsonify({"message": f"Insight {insight_id} fully updated."}), 200
            
        elif request.method == "PATCH":
            # Partially update status (e.g., changing risk level)
            return jsonify({"message": f"Insight {insight_id} partially updated."}), 200
            
        elif request.method == "DELETE":
            # Remove an insight or cancel a request
            return jsonify({"message": f"Insight {insight_id} deleted."}), 204

    # ERROR HANDLERS 

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "error": "Bad Request",
            "message": "Invalid geospatial data or parameters provided.",
            "code": 400
        }), 400

    @app.errorhandler(404)
    def resource_not_found(e):
        return jsonify({
            "error": "Not Found",
            "message": "The requested insight or satellite resource was not found.",
            "code": 404
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        """
        Directly addresses US-07 Acceptance Criteria:
        Given invalid method, when attempted, then 405 Method Not Allowed is returned.
        """
        return jsonify({
            "error": "Method Not Allowed",
            "message": "The requested HTTP method is not supported for this GeoScope endpoint.",
            "code": 405
        }), 405

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            "error": "Internal Server Error",
            "message": "An unexpected error occurred processing satellite imagery data.",
            "code": 500
        }), 500