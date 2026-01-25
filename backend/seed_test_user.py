from app.db import SessionLocal
from app.routes.observation import User, Subscription
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_test_user():
    db = SessionLocal()
    try:
        email = "testuser@geoscope.com"
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists.")
            # Ensure password and verification status are correct (optional update)
            existing_user.password = generate_password_hash("password123")
            existing_user.is_verified = 1
            existing_user.is_2fa_enabled = 0 # Default to disabled for easy testing initially, enable if testing 2FA
            db.commit()
            print(f"User {email} updated.")
        else:
            new_user = User(
                email=email,
                password=generate_password_hash("password123"),
                first_name="Test",
                last_name="User",
                is_2fa_enabled=0,
                is_verified=1, # Auto verify
                otp_code=None,
                otp_created_at=None
            )
            db.add(new_user)
            db.commit()
            print(f"User {email} created.")

        # Add Subscriptions
        # Add a subscription for product 1 for testing protected routes accessible
        existing_sub = db.query(Subscription).filter(Subscription.user_id == email, Subscription.product_id == 1).first()
        if not existing_sub:
             db.add(Subscription(user_id=email, product_id=1))
             db.commit()
             print(f"Subscription for product 1 added for {email}")
        
    except Exception as e:
        print(f"Error seeding test user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_user()
