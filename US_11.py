"""
US-11: Protect Historical Data

This module implements immutability protection for historical data.
Prevents edits to records created before the current quarter.
"""

from flask import request, jsonify
from datetime import datetime
from functools import wraps
# Import the actual model from your US_10 file
from US_10 import ObservationRecord

def get_current_quarter_start():
    """
    Get the start date of the current quarter.
    Q1: Jan 1, Q2: Apr 1, Q3: Jul 1, Q4: Oct 1
    """
    now = datetime.utcnow()
    quarter = (now.month - 1) // 3 + 1
    month_start = (quarter - 1) * 3 + 1
    return datetime(now.year, month_start, 1)

def protect_historical_data(db_model, session):
    """
    Decorator to protect historical data from being modified.
    Now accepts the session to perform queries correctly.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            record_id = kwargs.get('record_id')
            if not record_id:
                return jsonify({'error': 'Record ID required'}), 400
            
            try:
                # Use the session passed from the main app
                record = session.query(db_model).filter_by(id=record_id).first()
                if not record:
                    return jsonify({'error': 'Record not found'}), 404
                
                current_quarter_start = get_current_quarter_start()
                if record.timestamp < current_quarter_start:
                    return jsonify({
                        'error': 'Forbidden: Cannot modify historical records from previous quarters'
                    }), 403
                
                return func(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return wrapper
    return decorator

def register(app, session):
    """Registers protected PUT and DELETE routes."""

    @app.route('/api/observations/<int:obs_id>', methods=['PUT'])
    def update_obs(obs_id):
        obs = session.query(ObservationRecord).get(obs_id)
        if not obs: 
            return jsonify({'error': 'Not found'}), 404
        
        # --- US-11: Historical Integrity Check ---
        now = datetime.utcnow()
        # Find the month the current quarter started (Jan=1, Apr=4, Jul=7, Oct=10)
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        current_quarter_start = datetime(now.year, quarter_start_month, 1)

        # If the observation was created before this quarter, block the edit
        if obs.timestamp < current_quarter_start:
            return jsonify({
                'error': 'Historical Integrity Violation',
                'message': 'Records from previous quarters cannot be modified.'
            }), 403 # Forbidden
        # ------------------------------------------

        data = request.get_json()
        for key, value in data.items():
            if hasattr(obs, key):
                setattr(obs, key, value)
        
        session.commit()
        return jsonify({'message': 'Updated successfully'}), 200
    
    @app.route('/api/observations/<int:record_id>', methods=['DELETE'])
    @protect_historical_data(ObservationRecord, session)
    def delete_observation(record_id):
        try:
            record = session.query(ObservationRecord).filter_by(id=record_id).first()
            session.delete(record)
            session.commit()
            return jsonify({'message': 'Record deleted successfully'}), 200
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500