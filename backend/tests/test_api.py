import pytest
from fastapi.testclient import TestClient

from backend.main import app, build_allowed_origins

client = TestClient(app)


def status_of(device_id: str) -> str:
    devices = client.get("/devices").json()["devices"]
    return next(device["status"] for device in devices if device["id"] == device_id)


def test_health_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {
        "message": "Smart Home Controller API is running",
        "status": "ok",
    }


def test_get_devices_returns_names_and_statuses():
    response = client.get("/devices")

    assert response.status_code == 200
    devices = response.json()["devices"]
    assert [device["id"] for device in devices] == ["light", "fan", "ac"]
    assert [device["name"] for device in devices] == [
        "Light",
        "Fan",
        "Air Conditioner",
    ]
    assert [device["status"] for device in devices] == ["ON", "OFF", "ON"]


@pytest.mark.parametrize("device_id", ["light", "fan", "ac"])
def test_device_on_and_off_endpoints(device_id):
    off_response = client.post(f"/devices/{device_id}/off")

    assert off_response.status_code == 200
    assert off_response.json()["status"] == "OFF"
    assert off_response.json()["id"] == device_id
    assert status_of(device_id) == "OFF"

    on_response = client.post(f"/devices/{device_id}/on")

    assert on_response.status_code == 200
    assert on_response.json()["status"] == "ON"
    assert on_response.json()["message"]
    assert status_of(device_id) == "ON"


@pytest.mark.parametrize("action", ["on", "off"])
def test_invalid_device_id_returns_404(action):
    response = client.post(f"/devices/not-a-device/{action}")

    assert response.status_code == 404
    assert "not-a-device" in response.json()["detail"]


def test_cors_includes_configured_frontend_origin(monkeypatch):
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://homecontrol-app.vercel.app")

    origins = build_allowed_origins()

    assert "https://homecontrol-app.vercel.app" in origins
    assert "http://localhost:5173" in origins
    assert "*" not in origins


def test_cors_defaults_include_production_and_dev_origins(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)

    assert set(build_allowed_origins()) == {
        "https://homecontrol-app.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    }


def test_cors_supports_multiple_comma_separated_origins(monkeypatch):
    monkeypatch.setenv(
        "FRONTEND_ORIGIN",
        "https://homecontrol-app.vercel.app, https://homecontrol-app-git-main.vercel.app",
    )
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "https://preview.example.com")

    origins = build_allowed_origins()
    assert "https://homecontrol-app.vercel.app" in origins
    assert "https://homecontrol-app-git-main.vercel.app" in origins
    assert "https://preview.example.com" in origins
    assert "*" not in origins


def test_cors_preflight_for_vercel_origin():
    response = client.options(
        "/devices",
        headers={
            "Origin": "https://homecontrol-app.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://homecontrol-app.vercel.app"
    assert "GET" in response.headers["access-control-allow-methods"]

    get_response = client.get(
        "/devices", headers={"Origin": "https://homecontrol-app.vercel.app"}
    )
    assert get_response.status_code == 200
    assert get_response.headers["access-control-allow-origin"] == "https://homecontrol-app.vercel.app"


def test_cors_preflight_for_vercel_preview_origin():
    preview_origin = "https://homecontrol-app-git-main-example.vercel.app"
    response = client.options(
        "/rooms",
        headers={
            "Origin": preview_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == preview_origin

    rejected = client.options(
        "/rooms",
        headers={
            "Origin": "https://unrelated-site.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert rejected.status_code == 400
    assert "access-control-allow-origin" not in rejected.headers
