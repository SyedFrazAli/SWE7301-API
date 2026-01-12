"""
US-09: Filter and Retrieve Geospatial Observation Data
"""
from flask import request, jsonify
from US_10 import ObservationRecord # Import the model from your storage module

def register(app, session):
    """
    Registers the filtering routes for US-09.
    """
    
    @app.route('/api/observations/filter', methods=['GET'])
    def filter_observations():
        try:
            # 1. Get query parameters from the URL
            satellite_id = request.args.get('satellite_id')
            timezone = request.args.get('timezone')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')

            # 2. Start building the query
            query = session.query(ObservationRecord)

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