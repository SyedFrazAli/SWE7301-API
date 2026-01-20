from flask import request, jsonify, g
from app.routes.observation import ObservationRecord

def get_db():
    """Helper to get the current request's DB session"""
    return g.db

def register(app):
    """
    Registers GeoScope Bulk Retrieval.
    Fulfills US-12 (Updated): Efficiently fetching multiple records in one request.
    """

    @app.route("/api/v1/bulk/insights", methods=["GET"])
    def get_multiple_insights():
        db = get_db()  # per-request session

        # Get comma-separated IDs from query param
        ids_param = request.args.get('ids')
        if not ids_param:
            return jsonify({
                "error": "Bad Request",
                "message": "Please provide a comma-separated list of IDs in the 'ids' query parameter.",
                "code": 400
            }), 400

        try:
            id_list = [int(i.strip()) for i in ids_param.split(',')]
        except ValueError:
            return jsonify({
                "error": "Bad Request",
                "message": "IDs must be numeric.",
                "code": 400
            }), 400

        # Query the database for all matching IDs at once
        records = db.query(ObservationRecord).filter(ObservationRecord.id.in_(id_list)).all()

        # Build successful and failed lists
        found_ids = {r.id for r in records}
        successful = [r.to_dict() for r in records]
        failed = [{"id": i, "error": "Record not found"} for i in id_list if i not in found_ids]

        # Return results with metadata
        return jsonify({
            "results": successful,
            "metadata": {
                "total_requested": len(id_list),
                "found": len(successful),
                "failed_count": len(failed),
                "failures": failed
            }
        }), 200
