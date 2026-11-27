import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.container import get_container
from backend.domain import PowerAction
from backend.main import app

client = TestClient(app)


def test_device_status_includes_connectivity_room_and_energy():
    response = client.get("/devices/light/status")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "light"
    assert body["online"] is True
    assert body["room_id"] == "living-room"
    assert body["wattage"] == 60.0
    assert body["energy_wh"] >= 0


def test_offline_devices_reject_power_changes():
    assert client.post("/devices/fan/offline").status_code == 200
    response = client.post("/devices/fan/on")
    assert response.status_code == 409
    assert response.json()["code"] == "device_offline"
    assert client.get("/devices/fan/status").json()["online"] is False
    assert client.post("/devices/fan/online").status_code == 200


def test_activity_history_records_state_and_connectivity():
    client.post("/devices/light/off")
    client.post("/devices/fan/offline")
    response = client.get("/activity", params={"device_id": "light"})
    assert response.status_code == 200
    events = response.json()["activity"]
    assert events[0]["action"] == "OFF"
    assert events[0]["source"] == "api"
    all_events = client.get("/activity").json()["activity"]
    assert any(item["action"] == "OFFLINE" for item in all_events)


def test_room_crud_and_device_assignment():
    rooms = client.get("/rooms").json()["rooms"]
    assert [room["id"] for room in rooms] == ["living-room", "bedroom"]
    assert rooms[0]["device_count"] == 2

    created = client.post(
        "/rooms", json={"name": "Kitchen", "description": "Cooking area"}
    )
    assert created.status_code == 201
    room_id = created.json()["id"]

    assigned = client.put(
        "/devices/light/room", json={"room_id": room_id}
    )
    assert assigned.status_code == 200
    assert assigned.json()["room_id"] == room_id
    assert len(client.get(f"/rooms/{room_id}/devices").json()["devices"]) == 1

    updated = client.put(f"/rooms/{room_id}", json={"name": "Kitchenette"})
    assert updated.json()["name"] == "Kitchenette"
    assert client.delete(f"/rooms/{room_id}").status_code == 204
    assert client.get("/devices/light/status").json()["room_id"] is None


def test_room_validation_and_conflicts():
    assert client.post("/rooms", json={"name": "  "}).status_code == 422
    assert client.post("/rooms", json={"name": "Living Room"}).status_code == 409
    assert client.get("/rooms/missing").status_code == 404


def test_schedule_crud_toggle_and_validation():
    payload = {
        "device_id": "light",
        "action": "OFF",
        "time": "07:30",
        "days": [0, 6],
    }
    created = client.post("/schedules", json=payload)
    assert created.status_code == 201
    schedule_id = created.json()["id"]
    assert created.json()["days"] == [0, 6]

    assert client.post(f"/schedules/{schedule_id}/toggle").json()["enabled"] is False
    assert client.put(
        f"/schedules/{schedule_id}", json={"time": "08:00"}
    ).json()["time"] == "08:00"
    assert client.delete(f"/schedules/{schedule_id}").status_code == 204
    assert client.delete(f"/schedules/{schedule_id}").status_code == 404

    assert client.post("/schedules", json={**payload, "time": "25:00"}).status_code == 422


def test_due_schedule_applies_action():
    container = get_container()
    schedule = container.schedule_service.create_schedule(
        "light", PowerAction.OFF, "07:30", (0,)
    )
    fired = container.schedule_service.run_due(
        datetime(2026, 1, 5, 7, 30, tzinfo=timezone.utc)
    )
    assert [item.id for item in fired] == [schedule.id]
    assert container.device_service.get_device("light").status == "OFF"
    assert container.schedule_service.run_due(
        datetime(2026, 1, 5, 7, 30, tzinfo=timezone.utc)
    ) == ()


def test_automation_rule_triggers_target_device():
    created = client.post(
        "/rules",
        json={
            "name": "Light starts fan",
            "trigger_device_id": "light",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    assert created.status_code == 201
    assert created.json()["enabled"] is True

    client.post("/devices/light/off")
    client.post("/devices/light/on")
    assert client.get("/devices/fan/status").json()["status"] == "ON"
    assert any(
        item["source"] == "automation"
        for item in client.get("/activity").json()["activity"]
    )
    assert client.delete(f"/rules/{created.json()['id']}").status_code == 204


def test_energy_summary_and_detail():
    summary = client.get("/energy")
    assert summary.status_code == 200
    body = summary.json()
    assert len(body["devices"]) == 3
    assert body["total_wh"] >= 0
    assert client.get("/energy/ac").json()["wattage"] == 1200.0
    assert client.get("/energy/missing").status_code == 404


def test_notifications_created_read_and_deleted():
    client.post("/devices/light/off")
    listing = client.get("/notifications")
    assert listing.status_code == 200
    assert listing.json()["unread_count"] >= 1
    notification_id = listing.json()["notifications"][0]["id"]

    assert client.post(f"/notifications/{notification_id}/read").json()["read"] is True
    assert client.get("/notifications").json()["unread_count"] == 0
    assert client.delete(f"/notifications/{notification_id}").status_code == 204
    assert client.post("/notifications/missing/read").status_code == 404
    client.delete("/notifications")
    assert client.get("/notifications").json()["notifications"] == []
