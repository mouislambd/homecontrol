from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import backend.domain as domain
from backend.container import get_container
from backend.domain import AutomationRule, DeviceStatus, PowerAction
from backend.main import app
from backend.repositories import InMemoryRepository
from backend.services import EnergyService

client = TestClient(app)


def test_original_devices_contract_is_unchanged():
    response = client.get("/devices")
    assert response.json() == {
        "devices": [
            {"id": "light", "name": "Light", "status": "ON"},
            {"id": "fan", "name": "Fan", "status": "OFF"},
            {"id": "ac", "name": "Air Conditioner", "status": "ON"},
        ]
    }
    action = client.post("/devices/fan/on").json()
    assert set(action) == {"id", "name", "status", "message"}
    assert action["message"] == "Fan is ON"


@pytest.mark.parametrize(
    "method,path,code",
    [
        ("get", "/rooms/missing", "room_not_found"),
        ("get", "/schedules/missing", "schedule_not_found"),
        ("put", "/schedules/missing", "schedule_not_found"),
        ("delete", "/schedules/missing", "schedule_not_found"),
        ("get", "/rules/missing", "rule_not_found"),
        ("delete", "/rules/missing", "rule_not_found"),
        ("get", "/energy/missing", "device_not_found"),
        ("get", "/devices/missing/status", "device_not_found"),
        ("post", "/notifications/missing/read", "notification_not_found"),
    ],
)
def test_custom_error_handler_returns_documented_shape(method, path, code):
    kwargs = {"json": {}} if method in ("put", "post") else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 404
    assert response.json()["code"] == code
    assert "detail" in response.json()


def test_unknown_device_in_schedule_and_rule_is_rejected():
    schedule = client.post(
        "/schedules",
        json={"device_id": "missing", "action": "ON", "time": "08:00"},
    )
    assert schedule.status_code == 404
    rule = client.post(
        "/rules",
        json={
            "name": "Test",
            "trigger_device_id": "missing",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    assert rule.status_code == 404


def test_query_parameter_bounds_are_enforced():
    assert client.get("/activity", params={"limit": 0}).status_code == 422
    assert client.get("/activity", params={"limit": 501}).status_code == 422
    assert client.get("/activity", params={"limit": 5}).status_code == 200


def test_blank_rule_name_is_rejected_at_both_boundaries():
    response = client.post(
        "/rules",
        json={
            "name": "   ",
            "trigger_device_id": "light",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    assert response.status_code == 422
    with pytest.raises(ValueError):
        AutomationRule("r", "  ", "light", DeviceStatus.ON, "fan", PowerAction.ON)


def test_automation_chain_is_capped():
    client.post("/devices/ac/off")
    client.post(
        "/rules",
        json={
            "name": "light to fan",
            "trigger_device_id": "light",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    client.post(
        "/rules",
        json={
            "name": "fan to ac",
            "trigger_device_id": "fan",
            "trigger_status": "ON",
            "target_device_id": "ac",
            "target_action": "ON",
        },
    )
    client.post("/devices/light/off")
    client.post("/devices/light/on")

    assert client.get("/devices/fan/status").json()["status"] == "ON"
    assert client.get("/devices/ac/status").json()["status"] == "OFF"


def test_failed_automation_creates_error_notification():
    client.post("/devices/fan/offline")
    client.post(
        "/rules",
        json={
            "name": "light to offline fan",
            "trigger_device_id": "light",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    client.post("/devices/light/off")
    client.post("/devices/light/on")

    notifications = client.get("/notifications").json()["notifications"]
    assert any(item["level"] == "error" for item in notifications)


def test_failed_schedule_creates_error_notification():
    container = get_container()
    container.device_service.set_online("light", False)
    schedule = container.schedule_service.create_schedule(
        "light", PowerAction.ON, "07:30", (0,)
    )
    fired = container.schedule_service.run_due(
        datetime(2026, 1, 5, 7, 30, tzinfo=timezone.utc)
    )
    assert fired == ()
    assert schedule.last_run is None
    assert any(
        item.level.value == "error"
        for item in container.notification_service.list_notifications()
    )


def test_disabled_and_wrong_weekday_schedules_do_not_fire():
    container = get_container()
    container.schedule_service.create_schedule(
        "light", PowerAction.OFF, "07:30", (0,), enabled=False
    )
    weekday = container.schedule_service.create_schedule(
        "light", PowerAction.OFF, "07:30", (0,)
    )
    moment = datetime(2026, 1, 6, 7, 30, tzinfo=timezone.utc)
    assert container.schedule_service.run_due(moment) == ()
    assert weekday.last_run is None


def test_energy_accumulates_between_state_changes(monkeypatch):
    moment = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock = {"now": moment}
    monkeypatch.setattr(domain, "utcnow", lambda: clock["now"])

    container = get_container()
    energy = EnergyService(container.device_repository)
    container.device_service.set_power("light", False)
    container.device_service.set_power("light", True)
    clock["now"] = moment + timedelta(hours=1)
    container.device_service.set_power("light", False)

    assert energy.reading_for("light").energy_wh == pytest.approx(60.0)
    assert energy.total_wh() == pytest.approx(60.0)


def test_repository_is_safe_under_concurrent_writes():
    repository = InMemoryRepository(key=lambda item: item.device_id)
    devices = [domain.BaseDevice(f"d{i}", f"Device {i}") for i in range(40)]

    def add(device):
        repository.add(device)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(add, devices))

    assert len(repository) == 40
    assert len(repository.get_all()) == 40
