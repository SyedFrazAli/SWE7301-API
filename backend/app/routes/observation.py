from flask import request, jsonify, g
from datetime import datetime, timezone, timedelta
import random
from sqlalchemy import Column, String, DateTime, Integer, Text, func, Float

from app.db import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    stripe_price_id = Column(String(100), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "stripe_price_id": self.stripe_price_id
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
    value = Column(String(50), nullable=True) # e.g. "0.85"
    unit = Column(String(20), nullable=True)  # e.g. "NDVI"
    confidence = Column(Float, nullable=True) # e.g. 98.5

    def to_dict(self):
        # Fetch product name if possible (this is a simple hack since we don't have a relationship defined properly here yet for simplicity)
        # In a real app, use SQLAlchemy relationships.
        product_name = f"Product #{self.product_id}"
        if self.product_id:
            from app.db import SessionLocal
            db = SessionLocal()
            prod = db.get(Product, self.product_id)
            if prod:
                product_name = prod.name
            db.close()

        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "timezone": self.timezone,
            "coordinates": self.coordinates,
            "satellite_id": self.satellite_id,
            "spectral_indices": self.spectral_indices,
            "notes": self.notes,
            "product_id": self.product_id,
            "product_name": product_name,
            "value": self.value,
            "unit": self.unit,
            "confidence": self.confidence
        }

class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    endpoint = Column(String(100))

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "endpoint": self.endpoint
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

def log_usage(endpoint_name):
    """Helper to log API usage"""
    try:
        db = get_db()
        new_usage = ApiUsage(endpoint=endpoint_name)
        db.add(new_usage)
        db.commit()
    except Exception as e:
        print(f"Error logging usage: {e}")

def register(app):
    @app.route("/api/observations", methods=["POST"])
    def create_obs():
        """
        Create a new observation.
        ---
        tags:
          - Observations
        security:
          - Bearer: []
        parameters:
          - in: body
            name: body
            schema:
              type: object
              required:
                - product_id
                - value
              properties:
                product_id:
                  type: integer
                  description: ID of the product
                value:
                  type: number
                  description: Observation value
                lat:
                  type: number
                lon:
                  type: number
        responses:
          201:
            description: Observation created
          400:
            description: Invalid input
        """
        db = get_db()
        data = request.get_json() or {}

        # Convert ISO 8601 timestamp string to datetime
        if "timestamp" in data and data["timestamp"]:
            data["timestamp"] = datetime.fromisoformat(
                data["timestamp"].replace("Z", "+00:00")
            )

        # Filter data to only include valid model fields
        valid_fields = ["product_id", "value", "timestamp", "confidence"]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        new_obs = ObservationRecord(**filtered_data)
        db.add(new_obs)
        db.commit()
        db.refresh(new_obs)  # ensure ORM maps back the ID
        
        # Log usage
        log_usage("POST /api/observations")
        
        return jsonify({"id": new_obs.id}), 201

    @app.route("/api/observations", methods=["GET"])
    @jwt_required()
    def list_obs():
        """
        List all observations.
        ---
        tags:
          - Observations
        security:
          - Bearer: []
        responses:
          200:
            description: List of observations
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  product_id:
                    type: integer
                  value:
                    type: number
                  timestamp:
                    type: string
        """
        current_user = get_jwt_identity()
        db = get_db()
        
        # Access Control: Filter by subscription
        # 1. Get user's subscriptions
        subs = db.query(Subscription).filter(Subscription.user_id == current_user).all()
        subscribed_product_ids = [s.product_id for s in subs]
        
        # 2. Check for Pro Plan (ID 5)
        is_pro = 5 in subscribed_product_ids
        
        query = db.query(ObservationRecord)
        
        if not is_pro:
            if not subscribed_product_ids:
                # No subscriptions (Free Plan) -> No access
                return jsonify([]), 200
            else:
                # Filter strictly to subscribed products
                query = query.filter(ObservationRecord.product_id.in_(subscribed_product_ids))
        
        observations = query.order_by(ObservationRecord.timestamp.desc()).all()
        
        # Log usage
        log_usage("GET /api/observations")
        
        return jsonify([o.to_dict() for o in observations])

    @app.route("/api/observations/<int:obs_id>", methods=["GET"])
    @jwt_required()
    def get_obs(obs_id):
        current_user = get_jwt_identity()
        db = get_db()
        obs = db.get(ObservationRecord, obs_id)
        if not obs:
            return jsonify({"error": "Not found"}), 404
        
        # Access control: check if user has subscription for the product OR Pro Plan (ID 5)
        if obs.product_id:
            sub = db.query(Subscription).filter(
                Subscription.user_id == current_user,
                (Subscription.product_id == obs.product_id) | (Subscription.product_id == 5)
            ).first()
            if not sub:
                return jsonify({"error": "Forbidden: Subscription required"}), 403

        if obs.product_id:
            sub = db.query(Subscription).filter(
                Subscription.user_id == current_user,
                (Subscription.product_id == obs.product_id) | (Subscription.product_id == 5)
            ).first()
            if not sub:
                return jsonify({"error": "Forbidden: Subscription required"}), 403

        # Log usage
        log_usage("GET /api/observations/:id")

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
        
        # Log usage
        log_usage("PUT /api/observations/:id")
        
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
        
        # Log usage
        log_usage("DELETE /api/observations/:id")
        
        return jsonify({"message": "Deleted"}), 200

    @app.route("/api/usage-stats", methods=["GET"])
    def get_usage_stats():
        """
        Get API usage statistics
        """
        db = get_db()
        
        # Get usage for the last hour, grouped by minute
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # SQLite-specific date truncation for grouping by minute
        # For SQLite: strftime('%Y-%m-%d %H:%M:00', timestamp)
        usage_data = db.query(
            func.strftime('%H:%M', ApiUsage.timestamp).label('time_bucket'),
            func.count(ApiUsage.id).label('count')
        ).filter(
            ApiUsage.timestamp >= one_hour_ago
        ).group_by(
            'time_bucket'
        ).order_by(
            'time_bucket'
        ).all()
        
        # Format for chart
        labels = []
        data = []
        
        for row in usage_data:
            labels.append(row.time_bucket)
            data.append(row.count)
            
        return jsonify({
            "labels": labels,
            "data": data,
            "total_calls_last_hour": sum(data)
        })

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

    @app.route("/api/subscriptions", methods=["DELETE"])
    def delete_subscription():
        db = get_db()
        # Expecting JSON body with user_id and product_id
        # In a real app with JWT, we should trust the token's user_id, 
        # but for this logic we'll require user_id in body match the requestor or admin logic.
        # For simplicity consistent with creation/listing:
        
        data = request.get_json() or {}
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        
        if not user_id or not product_id:
            return jsonify({"error": "Missing user_id or product_id"}), 400
            
        # Find subscription
        sub = db.query(Subscription).filter(
            Subscription.user_id == user_id, 
            Subscription.product_id == int(product_id)
        ).first()
        
        if not sub:
            return jsonify({"error": "Subscription not found"}), 404
            
        db.delete(sub)
        db.commit()
        
        return jsonify({"message": "Subscription cancelled"}), 200
    
    @app.route("/api/simulate-traffic", methods=["POST"])
    def simulate_traffic():
        """
        Simulate traffic by logging multiple API usage entries AND creating dummy observations.
        """
        try:
            db = get_db()
            # Generate 5 logs per call (for continuous simulation) for chart
            for _ in range(5):
                # 1. Log Usage (Fixing Chart)
                # Ensure we use the exact same timestamp logic as the query
                log_usage("GET /api/observations")
            
            # 2. Create Dummy Observation (Fixing Tabs / Product #0)
            # Create 1 realistic observation per tick so tabs populate
            product_id = random.randint(1, 4) # Valid products only
            new_obs = ObservationRecord(
                product_id=product_id,
                value=str(round(random.uniform(0.1, 0.9), 2)),
                unit="Index",
                confidence=round(random.uniform(80.0, 99.9), 1),
                notes="Simulated Data"
            )
            db.add(new_obs)
            db.commit()

            return jsonify({"message": "Traffic simulated successfully", "count": 5}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
