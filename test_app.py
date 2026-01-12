import pytest
from datetime import datetime
from app import get_app, SessionLocal, engine
from US_10 import Base, ObservationRecord

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

def test_historical_integrity_enforcement(client):
    """
    US-11 Acceptance Criteria: 
    Given an old record, when update attempted, then 403 error returned.
    """
    # 1. Manually seed an old record (October 2024) into the DB
    session = SessionLocal()
    old_record = ObservationRecord(
        timestamp=datetime(2024, 10, 1), 
        timezone="GMT",
        coordinates="53.0, -2.0",
        satellite_id="HISTORICAL-SAT",
        notes="Historical data"
    )
    session.add(old_record)
    session.commit()
    record_id = old_record.id
    session.close()

    # 2. Attempt to update this record via the API
    update_data = {"notes": "Attempting to change history"}
    response = client.put(f'/api/observations/{record_id}', json=update_data)

    # 3. Assertions
    assert response.status_code == 403
    assert "Historical Integrity Violation" in response.get_json()['error']

def test_current_quarter_update_allowed(client):
    """Verify that records from the current quarter CAN still be updated."""
    # 1. Seed a new record (current time)
    session = SessionLocal()
    new_record = ObservationRecord(
        timestamp=datetime.utcnow(),
        timezone="GMT",
        coordinates="53.0, -2.0",
        satellite_id="MODERN-SAT"
    )
    session.add(new_record)
    session.commit()
    record_id = new_record.id
    session.close()

    # 2. Attempt update
    response = client.put(f'/api/observations/{record_id}', json={"notes": "Updated"})
    
    # 3. Assertions
    assert response.status_code == 200