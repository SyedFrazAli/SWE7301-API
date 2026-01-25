from datetime import datetime, timezone, timedelta
from app.db import engine, Base, SessionLocal
from app.routes.observation import Product, Subscription, ObservationRecord, User
from werkzeug.security import generate_password_hash
import random

def seed_database():
    """Populate database with realistic GeoScope data"""
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("🗑️  Clearing existing data...")
        db.query(Subscription).delete()
        db.query(ObservationRecord).delete()
        db.query(Product).delete()
      
        
        # ============================================================
        # 1. CREATE PRODUCTS 
        # ============================================================
        print("\n📦 Creating Products...")
        
        products = [
            Product(
                name="Climate Monitor Pro",
                description="Real-time climate change indicators including temperature anomalies, sea ice extent, and carbon emissions tracking.",
                price="$299/mo"
            ),
            Product(
                name="Crop Health Analytics",
                description="Advanced vegetation indices (NDVI, EVI, SAVI) for precision agriculture and yield forecasting.",
                price="$199/mo"
            ),
            Product(
                name="Wildfire Risk Intelligence",
                description="Fire danger assessment using thermal imaging, drought indices, and fuel moisture content analysis.",
                price="$399/mo"
            ),
            Product(
                name="Deforestation Tracker",
                description="Detect illegal logging and monitor forest cover changes with weekly satellite imagery updates.",
                price="$249/mo"
            ),
            Product(
                name="Urban Expansion Monitor",
                description="Track city growth, infrastructure development, and land use changes for urban planning.",
                price="$179/mo"
            ),
            Product(
                name="Water Resource Management",
                description="Monitor reservoir levels, irrigation patterns, and water quality indicators from space.",
                price="$229/mo"
            ),
            Product(
                name="Disaster Response Suite",
                description="Rapid damage assessment for floods, earthquakes, and hurricanes using SAR and optical imagery.",
                price="$499/mo"
            ),
            Product(
                name="Ocean Monitoring",
                description="Sea surface temperature, algal blooms, oil spills, and marine pollution detection.",
                price="$279/mo"
            )
        ]
        
        db.add_all(products)
        db.commit()
        
        # Refresh to get IDs
        for p in products:
            db.refresh(p)
        
        print(f"✅ Created {len(products)} products")

        # ============================================================
        # 2. CREATE USERS (Admin + Demo Test User)
        # ============================================================
        print("\n👥 Seeding users...")
        users = [
            {
                "email": "admin@geoscope.com",
                "password": "password",
                "first_name": "Admin",
                "last_name": "User",
                "is_verified": 1,
                "is_2fa_enabled": 0
            },
            {
                "email": "testuser@geoscope.com",
                "password": "password123",
                "first_name": "Test",
                "last_name": "User",
                "is_verified": 1,
                "is_2fa_enabled": 0
            }
        ]

        for u in users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"- Updating user {u['email']}")
                existing.password = generate_password_hash(u["password"])
                existing.first_name = u["first_name"]
                existing.last_name = u["last_name"]
                existing.is_verified = u["is_verified"]
                existing.is_2fa_enabled = u["is_2fa_enabled"]
            else:
                print(f"- Creating user {u['email']}")
                new_user = User(
                    email=u["email"],
                    password=generate_password_hash(u["password"]),
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    is_verified=u["is_verified"],
                    is_2fa_enabled=u["is_2fa_enabled"]
                )
                db.add(new_user)
        db.commit()

        # ============================================================
        # 3. CREATE SUBSCRIPTIONS (Randomly assign some products)
        # ============================================================
        print("\n🔔 Creating subscriptions...")
        all_products = db.query(Product).all()
        admin = db.query(User).filter(User.email == "admin@geoscope.com").first()
        testuser = db.query(User).filter(User.email == "testuser@geoscope.com").first()

        # Clear existing subscriptions for these users to avoid duplicates
        if admin:
            db.query(Subscription).filter(Subscription.user_id == admin.email).delete()
        if testuser:
            db.query(Subscription).filter(Subscription.user_id == testuser.email).delete()

        # Assign subscriptions
        for p in random.sample(all_products, k=min(3, len(all_products))):
            db.add(Subscription(user_id=admin.email, product_id=p.id))
        for p in random.sample(all_products, k=min(2, len(all_products))):
            db.add(Subscription(user_id=testuser.email, product_id=p.id))
        db.commit()
        print("✅ Subscriptions created")

        # ============================================================
        # 4. CREATE SAMPLE OBSERVATIONS (linked to some products)
        # ============================================================
        print("\n🛰️  Creating sample observation records...")
        sample_coords = [
            "-33.865143,151.209900",
            "51.507351,-0.127758",
            "40.712776,-74.005974",
            "-1.292066,36.821945",
            "35.689487,139.691711"
        ]
        satellites = ["Landsat-9", "Sentinel-2", "MODIS", "PlanetScope"]

        observations = []
        now = datetime.now(timezone.utc)
        for i in range(8):
            obs = ObservationRecord(
                timestamp=(now - timedelta(days=random.randint(0, 90))),
                timezone="UTC",
                coordinates=random.choice(sample_coords),
                satellite_id=random.choice(satellites),
                spectral_indices=f"{{'NDVI': {round(random.uniform(0.2,0.9),2)}}}",
                notes="Synthetic seed observation",
                product_id=random.choice(all_products).id
            )
            observations.append(obs)

        db.add_all(observations)
        db.commit()
        print(f"✅ Created {len(observations)} observations")

    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()