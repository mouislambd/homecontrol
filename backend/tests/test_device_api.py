import pytest
from fastapi.testclient import TestClient

from backend.main import app, build_allowed_origins

client = TestClient(app)


def test_create_update_and_delete_device():
    created = client.post(
        "/devices",
        json={
            "id": "plug-1",
            "name": "Smart Plug",
            "device_type": "light",
            "wattage": 25,
            "room_id": "living-room",
        },
    )
    assert created.status_code == 201
    assert created.json()["id"] == "plug-1"
    assert created.json()["room_id"] == "living-room"

    updated = client.put(
        "/devices/plug-1", json={"name": "Desk Lamp", "wattage": 40}
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Desk Lamp"
    assert updated.json()["wattage"] == 40.0

    assert client.delete("/devices/plug-1").status_code == 204
    assert client.get("/devices/plug-1/status").status_code == 404
    assert client.delete("/devices/plug-1").status_code == 404


@pytest.mark.parametrize(
    "device_type,wattage,label",
    [
        ("light", 60, "Light"),
        ("fan", 75, "Fan"),
        ("ac", 1200, "Air Conditioner"),
    ],
)
def test_each_device_type_keeps_its_identity(device_type, wattage, label):
    device_id = f"{device_type}-new"
    created = client.post(
        "/devices",
        json={
            "id": device_id,
            "name": label,
            "device_type": device_type,
            "wattage": wattage,
        },
    )
    assert created.status_code == 201
    assert created.json()["device_type"] == device_type
    assert created.json()["name"] == label
    assert created.json()["wattage"] == wattage

    before = len(client.get("/devices").json()["devices"])

    updated = client.put(
        f"/devices/{device_id}", json={"name": f"Updated {label}", "wattage": wattage + 1}
    )
    assert updated.status_code == 200
    assert updated.json()["device_type"] == device_type

    refreshed = client.get(f"/devices/{device_id}/status")
    assert refreshed.json()["device_type"] == device_type
    assert refreshed.json()["wattage"] == wattage + 1
    assert client.get(f"/devices/{device_id}/status").json()["name"] == f"Updated {label}"
    assert len(client.get("/devices").json()["devices"]) == before

    assert client.post(f"/devices/{device_id}/on").status_code == 200
    assert client.get(f"/devices/{device_id}/status").json()["status"] == "ON"
    assert client.delete(f"/devices/{device_id}").status_code == 204


def test_device_creation_validation_and_conflicts():
    payload = {"id": "plug", "name": "Plug", "device_type": "light"}
    assert client.post("/devices", json=payload).status_code == 201
    assert client.post("/devices", json=payload).status_code == 409

    invalid = {**payload, "id": "bad id", "name": "   "}
    assert client.post("/devices", json=invalid).status_code == 422
    assert client.post("/devices", json={**payload, "id": "x2", "device_type": "tv"}).status_code == 422
    assert client.post("/devices", json={**payload, "id": "x3", "wattage": -1}).status_code == 422
    assert client.post("/devices", json={**payload, "id": "x4", "room_id": "missing"}).status_code == 404


def test_production_cors_does_not_include_localhost(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://example.vercel.app")
    origins = build_allowed_origins()
    assert "https://homecontrol-app.vercel.app" in origins
    assert "https://example.vercel.app" in origins
    assert "http://localhost:5173" not in origins


def test_production_cors_has_default_frontend_origin(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    monkeypatch.delenv("BACKEND_CORS_ORIGINS", raising=False)
    assert build_allowed_origins() == ["https://homecontrol-app.vercel.app"]


def test_energy_logs_endpoint_is_explicitly_labelled_as_estimated():
    response = client.get("/energy/logs")
    assert response.status_code == 200
    body = response.json()
    assert body["logs"] == []
    assert "Estimated" in body["note"]
    assert client.get("/energy/logs", params={"limit": 0}).status_code == 422
