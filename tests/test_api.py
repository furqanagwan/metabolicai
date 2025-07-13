from app.database import init_db

init_db()  # Ensures tables exist before tests run

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_flow_with_all_branches():
    # --- Create user
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
    assert r.json()["profile"]["user_id"] == "testuser"

    # --- PATCH user (valid partial)
    patch_payload = {"user_id": "testuser", "body_fat_pct": 14.0}
    r = client.patch("/user", json=patch_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 200
    assert r.json()["profile"]["body_fat_pct"] == 14.0

    # --- PATCH user (user does not exist)
    patch_payload = {"user_id": "ghost", "body_fat_pct": 12.0}
    r = client.patch("/user", json=patch_payload, headers={"X-API-Key": "changeme"})
    assert r.status_code == 404

    # --- GET user (valid)
    r = client.get("/user", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "testuser"

    # --- GET user (not found)
    r = client.get("/user", headers={"X-API-Key": "changeme", "X-User-Id": "nope"})
    assert r.status_code == 404

    # --- GET user (missing user_id header)
    r = client.get("/user", headers={"X-API-Key": "changeme"})
    assert r.status_code == 422  # FastAPI validation error

    # --- Add entries for TDEE and analytics
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

    # --- POST entry (missing required header)
    e = {"date": "2025-07-18", "weight": 77.8, "calories": 2050}
    r = client.post("/entry", json=e, headers={"X-API-Key": "changeme"})
    assert r.status_code == 422  # missing user id header

    # --- PATCH entry (existing)
    patch_entry_payload = {"date": "2025-07-17", "weight": 77.7}
    r = client.patch(
        "/entry",
        json=patch_entry_payload,
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 200
    assert r.json()["entry"]["weight"] == 77.7

    # --- PATCH entry (nonexistent date)
    patch_entry_payload = {"date": "2099-01-01", "weight": 60}
    r = client.patch(
        "/entry",
        json=patch_entry_payload,
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 404

    # --- PATCH entry (missing user header)
    patch_entry_payload = {"date": "2025-07-17", "weight": 76}
    r = client.patch(
        "/entry",
        json=patch_entry_payload,
        headers={"X-API-Key": "changeme"},
    )
    assert r.status_code == 422

    # --- GET history
    r = client.get(
        "/history", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
    )
    assert r.status_code == 200
    assert "entries" in r.json()
    assert len(r.json()["entries"]) >= 1

    # --- GET history (missing user_id)
    r = client.get("/history", headers={"X-API-Key": "changeme"})
    assert r.status_code == 422

    # --- GET TDEE (success)
    r = client.get("/tdee", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"})
    assert r.status_code == 200
    assert "tdee" in r.json()

    # --- GET TDEE (not enough data)
    # create new user with only 1 entry
    user2 = {
        "user_id": "minimal",
        "age": 25,
        "gender": "female",
        "height_cm": 170,
        "body_fat_pct": 22.0,
        "current_weight": 68.0,
    }
    r = client.post("/user", json=user2, headers={"X-API-Key": "changeme"})
    assert r.status_code == 200
    entry2 = {"date": "2025-07-10", "weight": 68, "calories": 1400}
    r = client.post(
        "/entry", json=entry2, headers={"X-API-Key": "changeme", "X-User-Id": "minimal"}
    )
    assert r.status_code == 200
    r = client.get("/tdee", headers={"X-API-Key": "changeme", "X-User-Id": "minimal"})
    assert r.status_code == 400

    # --- Analytics endpoint
    r = client.get(
        "/analytics", headers={"X-API-Key": "changeme", "X-User-Id": "testuser"}
    )
    assert r.status_code == 200
    data = r.json()
    assert "weight_change" in data
    assert "avg_calories" in data
    assert "tdee_trend" in data
    assert "feature_importance" in data

    # --- Analytics endpoint (not enough entries)
    r = client.get(
        "/analytics", headers={"X-API-Key": "changeme", "X-User-Id": "minimal"}
    )
    assert r.status_code == 400

    # --- Feature importance endpoint (enough data)
    r = client.get(
        "/analytics/feature-importance",
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    assert r.status_code == 200

    # --- Feature importance endpoint (not enough data)
    r = client.get(
        "/analytics/feature-importance",
        headers={"X-API-Key": "changeme", "X-User-Id": "minimal"},
    )
    assert r.status_code == 200 or r.status_code == 400

    # --- Root
    r = client.get("/")
    assert r.status_code == 200
    assert "msg" in r.json()

    # --- Wrong API key
    r = client.post("/user", json=user_payload, headers={"X-API-Key": "wrong"})
    assert r.status_code == 401

    # --- Completely missing API key (triggers FastAPI validation)
    r = client.post("/user", json=user_payload)
    assert r.status_code == 422

    # --- HEADERS case: empty X-User-Id header
    r = client.get("/user", headers={"X-API-Key": "changeme", "X-User-Id": ""})
    assert r.status_code == 400

    # --- HEADERS case: PATCH entry missing calories and weight (no error, partial update)
    patch_entry_payload = {"date": "2025-07-17"}
    r = client.patch(
        "/entry",
        json=patch_entry_payload,
        headers={"X-API-Key": "changeme", "X-User-Id": "testuser"},
    )
    # Should return 200 even if nothing is changed, but you may want to assert for fields as above.
    assert r.status_code == 200
