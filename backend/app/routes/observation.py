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

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    price = Column(String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price
        }

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    product_id = Column(Integer, nullable=False)
    status = Column(String(50), default="active")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "product_id": self.product_id,
            "status": self.status
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

        # US-11 logic (Quarterly Lock) removed as per descoping
        data = request.get_json() or {}
        
        # Update fields dynamically
        for key, value in data.items():
            if hasattr(obs, key):
                setattr(obs, key, value)

        db.commit()
        return jsonify({"message": "Updated"}), 200

    @app.route("/api/products", methods=["GET"])
    def get_products():
        """
        Get all available products
        ---
        responses:
          200:
            description: A list of products
        """
        db = get_db()
        products = db.query(Product).all()
        return jsonify([p.to_dict() for p in products])

    @app.route("/api/subscriptions", methods=["GET"])
    def get_subscriptions():
        """
        Get user subscriptions
        ---
        parameters:
          - name: username
            in: query
            type: string
            required: false
        responses:
          200:
            description: A list of subscriptions
        """
        username = request.args.get("username")
        db = get_db()
        if username:
            subs = db.query(Subscription).filter(Subscription.username == username).all()
        else:
            subs = db.query(Subscription).all()
        return jsonify([s.to_dict() for s in subs])

    @app.route("/api/subscriptions", methods=["POST"])
    def create_subscription():
        db = get_db()
        data = request.get_json() or {}
        if not data.get("username") or not data.get("product_id"):
            return jsonify({"error": "Missing username or product_id"}), 400
        
        new_sub = Subscription(
            username=data["username"],
            product_id=data["product_id"]
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return jsonify(new_sub.to_dict()), 201