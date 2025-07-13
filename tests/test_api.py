from app.database import init_db

init_db()  # Ensures tables exist before tests run

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_flow_with_all_branches():
    # -- Create user
    user_payload = {
        "user_id": "testuser",
        "age": 30,
        "gender": "male",
        "height_cm": 180,
        "body_fat_pct": 15.0,
        "current_weight": 80.0,
    }
    r = client.post("/user", json=user_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 200

    # -- Partial PATCH user (valid)
    patch_payload = {"user_id": "testuser", "body_fat_pct": 14.0}
    r = client.patch("/user", json=patch_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 200
    assert r.json()["profile"]["body_fat_pct"] == 14.0

    # -- PATCH user (nonexistent user)
    patch_payload = {"user_id": "ghost", "body_fat_pct": 12.0}
    r = client.patch("/user", json=patch_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 404

    # -- GET user (valid)
    r = client.get("/user", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"})
    assert r.status_code == 200

    # -- GET user (not found)
    r = client.get("/user", headers={"X-API-Key": "changeme", "X-User-Id": "nope"})
    assert r.status_code == 404

    # -- GET user (missing user_id header)
    r = client.get("/user", headers={"X-API-Key": "changeme"})
    assert r.status_code == 400

    # -- Auth errors (wrong API key)
    r = client.post("/user", json=user_payload, headers={"X-API-Key": "wrongkey"})
    assert r.status_code == 401

    # -- Add multiple entries (some missing fields)
    entries = [
        {"date": "2025-07-10", "weight": 80, "calories": 2300},
        {"date": "2025-07-11", "weight": 79.5, "calories": 2250},
        {"date": "2025-07-12", "weight": 79.2, "calories": 2230},
        {"date": "2025-07-13", "weight": 79, "calories": 2200},
        {"date": "2025-07-14", "weight": 78.7, "calories": 2180},
        {"date": "2025-07-15", "weight": 78.5, "calories": 2150},
        {"date": "2025-07-16", "weight": 78.2, "calories": 2100},
        {"date": "2025-07-17", "weight": 78.0, "calories": 2080},
        {"date": "2025-07-18", "calories": 2050},  # only calories
        {"date": "2025-07-19", "weight": 77.7},  # only weight
    ]
    for e in entries:
        r = client.post(
            "/entry", json=e, headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
        )
        assert r.status_code == 200

    # -- PATCH entry (valid)
    patch_entry = {"date": "2025-07-10", "weight": 79.8}
    r = client.patch(
        "/entry",
        json=patch_entry,
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 200

    # -- PATCH entry (non-existent entry)
    patch_entry = {"date": "2000-01-01", "weight": 70}
    r = client.patch(
        "/entry",
        json=patch_entry,
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 404

    # -- GET history
    r = client.get(
        "/history", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "entries" in data
    assert len(data["entries"]) >= 8

    # -- TDEE prediction (should work)
    r = client.get("/tdee", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"})
    assert r.status_code == 200
    assert "tdee" in r.json()

    # -- TDEE prediction (not enough data)
    client.post(
        "/user",
        json={"user_id": "barely", "age": 28, "gender": "female"},
        headers={"X-API-Key": "changeme"},
    )
    r = client.get("/tdee", headers={"X-API-Key": "changeme", "X-User-Id": "barely"})
    assert r.status_code == 400

    # -- Analytics endpoint (should work)
    r = client.get(
        "/analytics", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "weight_change" in data
    assert "avg_calories" in data
    assert "tdee_trend" in data
    assert "feature_importance" in data

    # -- Analytics endpoint (not enough entries)
    r = client.get(
        "/analytics", headers={"X-API-Key": "changeme", "X-User-Id": "barely"}
    )
    assert r.status_code == 400

    # -- Analytics feature-importance endpoint (should work)
    r = client.get(
        "/analytics/feature-importance",
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), dict)

    # -- Analytics feature-importance endpoint (no data)
    r = client.get(
        "/analytics/feature-importance",
        headers={"X-API-Key": "changeme", "X-User-Id": "barely"},
    )
    assert r.status_code == 400

    # -- Root endpoint
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["msg"] == "Welcome to MetabolicAI!"
