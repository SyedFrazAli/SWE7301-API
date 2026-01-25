"""
US-09: Filter and Retrieve Geospatial Observation Data
"""
from flask import request, jsonify, g
from app.routes.observation import ObservationRecord

def get_db():
    """Helper to get the current request's DB session"""
    return g.db

def register(app):
    """
    Registers the filtering routes for US-09.
    """
    
    @app.route('/api/observations/filter', methods=['GET'])
    def filter_observations():
        db = get_db()  # use per-request session
        try:
            # 1. Get query parameters from the URL
            satellite_id = request.args.get('satellite_id')
            timezone = request.args.get('timezone')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # 2. Start building the query
            query = db.query(ObservationRecord)

            # 3. Apply filters if they exist in the request
            if satellite_id:
                query = query.filter(ObservationRecord.satellite_id == satellite_id)
            
            if timezone:
                query = query.filter(ObservationRecord.timezone == timezone)
                
            if start_date:
                query = query.filter(ObservationRecord.timestamp >= start_date)
            
            if end_date:
                query = query.filter(ObservationRecord.timestamp <= end_date)

            # 4. Execute query and convert results to a list of dictionaries
            results = query.all()
            output = [obs.to_dict() for obs in results]

            return jsonify(output), 200

        except Exception as e:
            return jsonify({'error': str(e)}), 500
