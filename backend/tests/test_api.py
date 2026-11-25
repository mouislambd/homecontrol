import pytest
from fastapi.testclient import TestClient

from backend.main import app

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
