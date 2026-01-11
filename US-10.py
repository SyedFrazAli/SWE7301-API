"""US-10: Store Geospatial Observation Data

This module implements storage of geospatial observation data with
timestamp, timezone, coordinates, satellite_id, spectral indices, and notes.
"""

from flask import request, jsonify
from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ObservationRecord(Base):
    """Database model for geospatial observation records."""
    __tablename__ = 'observations'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    timezone = Column(String(50), nullable=False)
    coordinates = Column(Geometry('POINT'), nullable=False)
    satellite_id = Column(String(100), nullable=False)
    spectral_indices = Column(String(500))
    notes = Column(Text)
    
    def validate(self):
        """Validate required fields."""
        required_fields = ['timestamp', 'timezone', 'coordinates', 'satellite_id']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f'Missing required field: {field}')

def create_observation_endpoints(app, db):
    """Create endpoints for managing geospatial observations."""
    
    @app.route('/api/observations', methods=['POST'])
    def create_observation():
        try:
            data = request.get_json()
            observation = ObservationRecord(
                timestamp=data.get('timestamp'),
                timezone=data.get('timezone'),
                coordinates=data.get('coordinates'),
                satellite_id=data.get('satellite_id'),
                spectral_indices=data.get('spectral_indices'),
                notes=data.get('notes')
            )
            observation.validate()
            db.session.add(observation)
            db.session.commit()
            return jsonify({'id': observation.id, 'message': 'Observation created'}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/observations/<int:obs_id>', methods=['GET'])
    def get_observation(obs_id):
        try:
            obs = db.session.query(ObservationRecord).filter_by(id=obs_id).first()
            if not obs:
                return jsonify({'error': 'Observation not found'}), 404
            return jsonify({
                'id': obs.id,
                'timestamp': obs.timestamp.isoformat(),
                'timezone': obs.timezone,
                'coordinates': str(obs.coordinates),
                'satellite_id': obs.satellite_id
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
