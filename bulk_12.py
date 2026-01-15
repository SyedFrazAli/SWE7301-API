from flask import request, jsonify

def register(app, session=None):
    """
    Registers GeoScope Bulk Retrieval.
    Fulfills US-12 (Updated): Efficiently fetching multiple records in one request.
    """

    @app.route("/api/v1/bulk/insights", methods=["GET"])
    def get_multiple_insights():
        # AC-01: Process multiple records in a single request via ID list
        # Example URL: /api/v1/bulk/insights?ids=101,102,105
        ids_param = request.args.get('ids')
        
        if not ids_param:
            return jsonify({
                "error": "Bad Request",
                "message": "Please provide a comma-separated list of IDs in the 'ids' query parameter.",
                "code": 400
            }), 400

        try:
            id_list = [int(id.strip()) for id in ids_param.split(',')]
        except ValueError:
            return jsonify({
                "error": "Bad Request",
                "message": "IDs must be numeric.",
                "code": 400
            }), 400

        # Mock Database lookup
        mock_db = {
            101: {"id": 101, "type": "wildfire", "risk": "high"},
            102: {"id": 102, "type": "deforestation", "risk": "critical"}
        }

        successful = []
        failed = []

        # AC-02: Partial failure handling (identify which IDs were not found)
        for requested_id in id_list:
            if requested_id in mock_db:
                successful.append(mock_db[requested_id])
            else:
                failed.append({
                    "id": requested_id,
                    "error": "Record not found"
                })

        # Return 200 even with partial failure, but include the "failed" details
        return jsonify({
            "results": successful,
            "metadata": {
                "total_requested": len(id_list),
                "found": len(successful),
                "failed_count": len(failed),
                "failures": failed
            }
        }), 200