import os
import sys
import shutil
import tempfile
import sqlite3
from pathlib import Path
import pytest
from starlette.testclient import TestClient

# Workspace paths
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

ORIGINAL_DB = ROOT_DIR / "signalhunt.db"


@pytest.fixture
def client(monkeypatch):
    """
    Creates an isolated copy of signalhunt.db for each test run to ensure
    tests are completely independent, deterministic, and safe without altering production data.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_db = Path(tmp_dir) / "test_signalhunt.db"
        shutil.copyfile(ORIGINAL_DB, temp_db)

        # Ensure isolated test copy has a standardized baseline
        conn = sqlite3.connect(temp_db)
        conn.execute("UPDATE game_state SET status='waiting', started_at=NULL, paused_at=NULL, remaining_seconds=7200 WHERE id=1")
        conn.commit()
        conn.close()

        monkeypatch.setenv("DATABASE_PATH", str(temp_db))
        monkeypatch.setenv("ADMIN_PASSWORD", "TEST_ADMIN_SECRET")

        # Import or reload app with new env
        from app.main import app, rate_limiter
        rate_limiter.reset()

        with TestClient(app) as test_client:
            yield test_client, temp_db


def test_cors_preflight_and_headers(client):
    test_client, _ = client

    # Preflight OPTIONS request from Render frontend origin
    res = test_client.options(
        "/api/login",
        headers={
            "Origin": "https://riyazomer11343.onrender.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://riyazomer11343.onrender.com"
    assert "POST" in res.headers.get("access-control-allow-methods", "")

    # Preflight from localhost
    res_local = test_client.options(
        "/api/status",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_local.status_code == 200
    assert res_local.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_public_status_initial_state_and_invariance(client):
    test_client, _ = client

    # Verify initial timer is waiting with 7200s (2 hours)
    res = test_client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "waiting"
    assert data["remaining_seconds"] == 7200
    assert data["duration_seconds"] == 7200

    # Verify repeated status calls do not restart or alter timer
    for _ in range(5):
        r = test_client.get("/api/status")
        d = r.json()
        assert d["status"] == "waiting"
        assert d["remaining_seconds"] == 7200


def test_login_success_and_colour_compatibility(client):
    test_client, db_path = client

    # Extract valid code from the database for Team Red
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    red_team = conn.execute("SELECT * FROM teams WHERE colour='red'").fetchone()
    conn.close()
    assert red_team is not None

    # We know the demo code for Team Red is REDRACERS2026
    # Let's test login with valid code
    res = test_client.post(
        "/api/login",
        json={
            "code": "REDRACERS2026",
            "device_id": "test_device_001",
            "colour": "red",
            "color": "red"
        }
    )
    assert res.status_code == 200
    data = res.json()

    # Verify response structure has required fields
    assert "team" in data
    assert "status" in data
    assert "remaining_seconds" in data
    assert "current_clue" in data
    assert "progress" in data

    # Verify team object contains both 'colour' and 'color' for compatibility
    team = data["team"]
    assert team["id"] == red_team["id"]
    assert team["colour"] == "red"
    assert team["color"] == "red"
    assert team["name"] == "Team Red"


def test_login_invalid_code_friendly_error(client):
    test_client, _ = client

    res = test_client.post(
        "/api/login",
        json={
            "code": "TOTALLY_INVALID_CODE_1234",
            "device_id": "test_device_002",
            "colour": "red"
        }
    )
    assert res.status_code == 401
    data = res.json()
    assert "Invalid team code" in data.get("detail", "")


def test_login_colour_mismatch_error(client):
    test_client, _ = client

    # Code for Red team, but user selected Yellow team
    res = test_client.post(
        "/api/login",
        json={
            "code": "REDRACERS2026",
            "device_id": "test_device_003",
            "colour": "yellow",
            "color": "yellow"
        }
    )
    assert res.status_code == 400
    data = res.json()
    assert "Access code does not belong to the selected team" in data.get("detail", "")


def test_organizer_authorization(client):
    test_client, _ = client

    # Unauthorized attempt to start game
    res_no_auth = test_client.post("/api/admin/game/start")
    assert res_no_auth.status_code == 401

    # Unauthorized attempt with bad password
    res_bad_auth = test_client.post(
        "/api/admin/game/start",
        headers={"X-Admin-Password": "WRONG_PASSWORD"}
    )
    assert res_bad_auth.status_code == 401

    # Unauthorized attempt to init game (new endpoint)
    res_init_no_auth = test_client.post("/api/admin/game/init")
    assert res_init_no_auth.status_code == 401

    res_init_bad_auth = test_client.post(
        "/api/admin/game/init",
        headers={"X-Admin-Password": "WRONG_PASSWORD"}
    )
    assert res_init_bad_auth.status_code == 401


def test_start_game_from_finished_state(client):
    test_client, db_path = client

    # Simulate database in finished state (matching the original BUG 2 production state)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE game_state SET status='finished', started_at=NULL, paused_at=NULL, remaining_seconds=0 WHERE id=1")
    conn.commit()
    conn.close()

    # Public status reports finished
    res_status = test_client.get("/api/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "finished"

    # Organizer starts new 2-hour event directly from finished state
    res_start = test_client.post(
        "/api/admin/game/start",
        headers={"X-Admin-Password": "TEST_ADMIN_SECRET"}
    )
    assert res_start.status_code == 200
    data = res_start.json()
    assert data["status"] == "active"
    assert data["remaining_seconds"] == 7200


def test_organizer_start_timer_and_status_progression(client):
    test_client, _ = client

    # Start game as organizer
    res = test_client.post(
        "/api/admin/game/start",
        headers={"X-Admin-Password": "TEST_ADMIN_SECRET"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["remaining_seconds"] == 7200

    # Public status should now report active
    res_status = test_client.get("/api/status")
    assert res_status.status_code == 200
    st = res_status.json()
    assert st["status"] == "active"
    assert 7190 <= st["remaining_seconds"] <= 7200

    # Ordinary status requests must not restart the timer
    res_status2 = test_client.get("/api/status")
    assert res_status2.json()["status"] == "active"


def test_organizer_init_game_safe_reset(client):
    test_client, db_path = client

    # Start the game first
    test_client.post(
        "/api/admin/game/start",
        headers={"X-Admin-Password": "TEST_ADMIN_SECRET"}
    )

    # Now safely initialize the timer state without touching data
    res_init = test_client.post(
        "/api/admin/game/init",
        headers={"X-Admin-Password": "TEST_ADMIN_SECRET"}
    )
    assert res_init.status_code == 200
    data = res_init.json()
    assert data["status"] == "waiting"
    assert data["remaining_seconds"] == 7200

    # Verify all 12 teams and 16 clues remain intact
    conn = sqlite3.connect(db_path)
    team_count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    clue_count = conn.execute("SELECT COUNT(*) FROM clues").fetchone()[0]
    conn.close()
    assert team_count == 12
    assert clue_count == 16


def test_team_capacity_limit(client):
    test_client, db_path = client

    # Clear participants in temporary test database to test exact 5-slot allocation
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM participants")
    conn.commit()
    conn.close()

    # Max 5 participants per team
    for i in range(5):
        r = test_client.post(
            "/api/login",
            json={
                "code": "REDRACERS2026",
                "device_id": f"device_slot_{i}",
                "colour": "red"
            }
        )
        assert r.status_code == 200

    # 6th participant on same team should be rejected
    r6 = test_client.post(
        "/api/login",
        json={
            "code": "REDRACERS2026",
            "device_id": "device_slot_overflow",
            "colour": "red"
        }
    )
    assert r6.status_code == 403
    assert "Team participant limit reached" in r6.json().get("detail", "")


def test_admin_overview_structure(client):
    test_client, _ = client

    res = test_client.get(
        "/api/admin/overview",
        headers={"X-Admin-Password": "TEST_ADMIN_SECRET"}
    )
    assert res.status_code == 200
    data = res.json()

    assert "game_state" in data
    assert "teams" in data
    assert "clues" in data
    assert len(data["teams"]) == 12
    assert len(data["clues"]) == 16

    # Verify team fields have colour and color
    for t in data["teams"]:
        assert "colour" in t
        assert "color" in t
        assert t["colour"] == t["color"]
