from flask import request, jsonify, g
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text
from app.db import Base

class ObservationRecord(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    timezone = Column(String(50))
    coordinates = Column(String(255))
    satellite_id = Column(String(100))
    spectral_indices = Column(String(500))
    notes = Column(Text)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timezone": self.timezone,
            "coordinates": self.coordinates,
            "satellite_id": self.satellite_id,
            "spectral_indices": self.spectral_indices,
            "notes": self.notes,
        }

def get_db():
    """Helper to get the current request's DB session"""
    return g.db

def register(app):
    @app.route("/api/observations", methods=["POST"])
    def create_obs():
        db = get_db()
        data = request.get_json() or {}

        # Convert ISO 8601 timestamp string to datetime
        if "timestamp" in data and data["timestamp"]:
            data["timestamp"] = datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            )

        new_obs = ObservationRecord(**data)
        db.add(new_obs)
        db.commit()
        db.refresh(new_obs)  # ensure ORM maps back the ID
        return jsonify({"id": new_obs.id}), 201

    @app.route("/api/observations/<int:obs_id>", methods=["GET"])
    def get_obs(obs_id):
        db = get_db()
        obs = db.get(ObservationRecord, obs_id)
        if not obs:
            return jsonify({"error": "Not found"}), 404
        return jsonify(obs.to_dict())

    @app.route("/api/observations/<int:obs_id>", methods=["PUT"])
    def update_obs(obs_id):
        db = get_db()
        obs = db.get(ObservationRecord, obs_id)
        if not obs:
            return jsonify({"error": "Not found"}), 404

        # Prevent editing records from previous quarters
        now = datetime.now(timezone.utc)
        q_start_month = ((now.month - 1) // 3) * 3 + 1
        current_q_start = datetime(now.year, q_start_month, 1, tzinfo=timezone.utc)

        if obs.timestamp < current_q_start:
            return jsonify({
                "error": "Historical Integrity Violation",
                "message": "Cannot modify records from previous quarters."
            }), 403

        data = request.get_json() or {}
        for key, value in data.items():
            if hasattr(obs, key):
                setattr(obs, key, value)

        db.commit()
        return jsonify({"message": "Updated"}), 200
