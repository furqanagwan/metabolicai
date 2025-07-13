from app.database import init_db

init_db()  # <- Ensures tables exist before tests run

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_user_and_entry_flow():
    user_payload = {
        "user_id": "testuser",
        "age": 30,
        "gender": "male",
        "height_cm": 180,
        "body_fat_pct": 15.0,
        "current_weight": 80.0,
    }
    # Create user
    r = client.post("/user", json=user_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 200

    # Add multiple entries
    entries = [
        {"date": "2025-07-10", "weight": 80, "calories": 2300},
        {"date": "2025-07-11", "weight": 79.5, "calories": 2250},
        {"date": "2025-07-12", "weight": 79.2, "calories": 2230},
        {"date": "2025-07-13", "weight": 79, "calories": 2200},
        {"date": "2025-07-14", "weight": 78.7, "calories": 2180},
        {"date": "2025-07-15", "weight": 78.5, "calories": 2150},
        {"date": "2025-07-16", "weight": 78.2, "calories": 2100},
        {"date": "2025-07-17", "weight": 78.0, "calories": 2080},
    ]
    for e in entries:
        r = client.post(
            "/entry", json=e, headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
        )
        assert r.status_code == 200

    # TDEE prediction
    r = client.get("/tdee", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"})
    assert r.status_code == 200
    assert "tdee" in r.json()

    # Analytics endpoint
    r = client.get(
        "/analytics", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "weight_change" in data
    assert "avg_calories" in data
    assert "tdee_trend" in data
    assert "feature_importance" in data
