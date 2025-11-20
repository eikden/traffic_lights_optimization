import pytest

pytest.importorskip("fastapi")
pytest.importorskip("yaml")

from pathlib import Path

from fastapi.testclient import TestClient

from src.web.app import create_app


def test_portal_login_and_run_simulation(tmp_path):
    app = create_app(config_dir=Path("configs"))
    client = TestClient(app)

    unauthorized = client.get("/dashboard")
    assert unauthorized.status_code == 401

    login = client.post("/login", data={"username": "admin", "password": "admin"}, allow_redirects=False)
    assert login.status_code == 302

    cookies = login.cookies
    response = client.post(
        "/api/simulations",
        data={"layout": "bukit_bintang_crossing", "steps": 20, "arrival_intensity": 0.5, "crossing_rate": 0.1},
        cookies=cookies,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["avg_queue"] >= 0

    analytics = client.get("/api/analytics", cookies=cookies)
    assert analytics.status_code == 200
    assert analytics.json()["runs"] >= 1

    export = client.get(f"/api/simulations/{payload['id']}/omniverse", cookies=cookies)
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("application/json")
