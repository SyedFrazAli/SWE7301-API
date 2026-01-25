from flask import request, jsonify, g
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text
from app.db import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
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
    user_id = Column(String(100), nullable=False)
    product_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ObservationRecord(Base):
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    timezone = Column(String(50))
    coordinates = Column(String(255))
    satellite_id = Column(String(100))
    spectral_indices = Column(String(500))
    notes = Column(Text)
    product_id = Column(Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timezone": self.timezone,
            "coordinates": self.coordinates,
            "satellite_id": self.satellite_id,
            "spectral_indices": self.spectral_indices,
            "notes": self.notes,
            "product_id": self.product_id,
        }

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=True)  # Nullable for OAuth users
    first_name = Column(String(100))
    last_name = Column(String(100))
    otp_secret = Column(String(100), nullable=True)
    is_2fa_enabled = Column(Integer, default=0) # SQLite doesn't have Boolean, use Integer (0/1)
    is_verified = Column(Integer, default=0) # Email verification status
    otp_code = Column(String(10), nullable=True) # Current OTP
    otp_created_at = Column(DateTime, nullable=True) # OTP timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_2fa_enabled": bool(self.is_2fa_enabled),
            "is_verified": bool(self.is_verified)
        }

from flask_jwt_extended import jwt_required, get_jwt_identity

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
    @jwt_required()
    def get_obs(obs_id):
        current_user = get_jwt_identity()
        db = get_db()
        obs = db.get(ObservationRecord, obs_id)
        if not obs:
            return jsonify({"error": "Not found"}), 404
        
        # Access control: check if user has subscription for the product
        if obs.product_id:
            sub = db.query(Subscription).filter(
                Subscription.user_id == current_user,
                Subscription.product_id == obs.product_id
            ).first()
            if not sub:
                return jsonify({"error": "Forbidden: Subscription required"}), 403

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

    @app.route("/api/observations/<int:obs_id>", methods=["DELETE"])
    def delete_obs(obs_id):
        """
        Delete an observation record
        ---
        parameters:
          - name: obs_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Deleted successfully
          404:
            description: Not found
        """
        db = get_db()
        obs = db.get(ObservationRecord, obs_id)
        if not obs:
            return jsonify({"error": "Not found"}), 404
        
        db.delete(obs)
        db.commit()
        return jsonify({"message": "Deleted"}), 200

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
          - name: user_id
            in: query
            type: string
            required: false
        responses:
          200:
            description: A list of subscriptions
        """
        user_id = request.args.get("user_id")
        db = get_db()
        if user_id:
            subs = db.query(Subscription).filter(Subscription.user_id == user_id).all()
        else:
            subs = db.query(Subscription).all()
        return jsonify([s.to_dict() for s in subs])

    @app.route("/api/subscriptions", methods=["POST"])
    def create_subscription():
        db = get_db()
        data = request.get_json() or {}
        if not data.get("user_id") or not data.get("product_id"):
            return jsonify({"error": "Missing user_id or product_id"}), 400
        
        new_sub = Subscription(
            user_id=data["user_id"],
            product_id=data["product_id"]
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return jsonify(new_sub.to_dict()), 201
