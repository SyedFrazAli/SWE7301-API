# backend/tests/test_app.py
import pytest
from datetime import datetime, timezone
from run import get_app
from app.db import engine
from sqlalchemy.orm import sessionmaker
from app.routes.observation import Base, ObservationRecord

# Create a session factory
SessionLocal = sessionmaker(bind=engine)

@pytest.fixture
def client():
    # Ensure tables are created
    Base.metadata.create_all(engine)
    
    app = get_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client

    # Cleanup after test
    Base.metadata.drop_all(engine)
#Descoped test for US-11
# def test_historical_integrity_enforcement(client):
#     """
#     US-11 Acceptance Criteria: 
#     Given an old record, when update attempted, then 403 error returned.
#     """
#     session = SessionLocal()
#     old_record = ObservationRecord(
#         timestamp=datetime(2024, 10, 1, tzinfo=timezone.utc), 
#         timezone="GMT",
#         coordinates="53.0, -2.0",
#         satellite_id="HISTORICAL-SAT",
#         notes="Historical data"
#     )
#     session.add(old_record)
#     session.commit()
#     record_id = old_record.id
#     session.close()

#     update_data = {"notes": "Attempting to change history"}
#     response = client.put(f'/api/observations/{record_id}', json=update_data)

#     assert response.status_code == 403
#     assert "Historical Integrity Violation" in response.get_json()['error']

def test_current_quarter_update_allowed(client):
    """Verify that records from the current quarter CAN still be updated."""
    session = SessionLocal()
    new_record = ObservationRecord(
        timestamp=datetime.now(timezone.utc),
        timezone="GMT",
        coordinates="53.0, -2.0",
        satellite_id="MODERN-SAT"
    )
    session.add(new_record)
    session.commit()
    record_id = new_record.id
    session.close()

    response = client.put(f'/api/observations/{record_id}', json={"notes": "Updated"})
    assert response.status_code == 200
