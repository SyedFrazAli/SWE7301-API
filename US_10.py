from flask import request, jsonify
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.orm import declarative_base  # Fixes MovedIn20Warning

Base = declarative_base()

class ObservationRecord(Base):
    __tablename__ = 'observations'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    timezone = Column(String(50))
    coordinates = Column(String(255))
    satellite_id = Column(String(100))
    spectral_indices = Column(String(500))
    notes = Column(Text)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'timezone': self.timezone,
            'coordinates': self.coordinates,
            'satellite_id': self.satellite_id,
            'spectral_indices': self.spectral_indices,
            'notes': self.notes
        }

def register(app, session):
    @app.route('/api/observations', methods=['POST'])
    def create_obs():
        data = request.get_json()
        new_obs = ObservationRecord(**data)
        session.add(new_obs)
        session.commit()
        return jsonify({'id': new_obs.id}), 201

    @app.route('/api/observations/<int:obs_id>', methods=['GET'])
    def get_obs(obs_id):
        obs = session.query(ObservationRecord).get(obs_id)
        return jsonify(obs.to_dict()) if obs else (jsonify({'error': 'Not found'}), 404)

    @app.route('/api/observations/<int:obs_id>', methods=['PUT'])
    def update_obs(obs_id):
        obs = session.query(ObservationRecord).get(obs_id)
        if not obs:
            return jsonify({'error': 'Not found'}), 404

        # --- US-11: Historical Integrity Logic ---
        now = datetime.now()
        # Calculate start of current quarter
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        current_q_start = datetime(now.year, q_start_month, 1)

        if obs.timestamp < current_q_start:
            return jsonify({
                'error': 'Historical Integrity Violation',
                'message': 'Cannot modify records from previous quarters.'
            }), 403
        # ------------------------------------------

        data = request.get_json()
        for key, value in data.items():
            if hasattr(obs, key):
                setattr(obs, key, value)
        session.commit()
        return jsonify({'message': 'Updated'}), 200