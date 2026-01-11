"""US-11: Protect Historical Data

This module implements immutability protection for historical data.
Prevents edits to records created before the current quarter.
"""

from flask import request, jsonify
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from functools import wraps

def get_current_quarter_start():
    """
    Get the start date of the current quarter.
    Q1: Jan 1, Q2: Apr 1, Q3: Jul 1, Q4: Oct 1
    """
    now = datetime.utcnow()
    quarter = (now.month - 1) // 3 + 1
    month_start = (quarter - 1) * 3 + 1
    return datetime(now.year, month_start, 1)

def protect_historical_data(db_model):
    """
    Decorator to protect historical data from being modified.
    Allows updates only for records created in the current quarter.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            record_id = kwargs.get('record_id') or (args[0] if args else None)
            if not record_id:
                return jsonify({'error': 'Record ID required'}), 400
            
            try:
                record = db_model.query.filter_by(id=record_id).first()
                if not record:
                    return jsonify({'error': 'Record not found'}), 404
                
                current_quarter_start = get_current_quarter_start()
                if record.created_at < current_quarter_start:
                    return jsonify({
                        'error': 'Cannot modify historical records from previous quarters'
                    }), 403
                
                return func(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return wrapper
    return decorator

def create_protected_endpoints(app, ObservationModel, db):
    """
    Create REST endpoints with historical data protection.
    """
    @app.route('/api/observations/<int:record_id>', methods=['PUT'])
    @protect_historical_data(ObservationModel)
    def update_observation(record_id):
        try:
            record = ObservationModel.query.filter_by(id=record_id).first()
            data = request.get_json()
            
            for key, value in data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            
            db.session.commit()
            return jsonify({'message': 'Record updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/observations/<int:record_id>', methods=['DELETE'])
    @protect_historical_data(ObservationModel)
    def delete_observation(record_id):
        try:
            record = ObservationModel.query.filter_by(id=record_id).first()
            db.session.delete(record)
            db.session.commit()
            return jsonify({'message': 'Record deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

class ProtectedRecord:
    """Mixin class for models that need historical data protection."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def is_historical(self):
        """Check if this record is from a previous quarter."""
        return self.created_at < get_current_quarter_start()
