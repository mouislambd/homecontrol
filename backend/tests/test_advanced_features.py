from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.container import get_container
from backend.domain import AutomationRule, DeviceStatus, PowerAction, Schedule, TriggerType
from backend.main import app

client = TestClient(app)


def test_temperature_input_is_explicitly_simulated():
    response = client.put("/devices/ac/temperature", json={"value": 30})
    assert response.status_code == 200
    body = response.json()
    assert body["temperature_c"] == 30.0
    assert body["temperature_source"] == "simulated"
    assert client.put("/devices/ac/temperature", json={"value": 500}).status_code == 422
    assert client.put("/devices/ac/temperature", json={"value": "hot"}).status_code == 422


def test_threshold_rule_requires_threshold_and_executes():
    invalid = {
        "name": "Hot AC",
        "trigger_device_id": "ac",
        "trigger_type": "temperature_above",
        "target_device_id": "fan",
        "target_action": "ON",
    }
    assert client.post("/rules", json=invalid).status_code == 422

    created = client.post("/rules", json={**invalid, "threshold_c": 28})
    assert created.status_code == 201
    assert created.json()["trigger_type"] == "temperature_above"
    assert created.json()["threshold_c"] == 28.0

    client.put("/devices/ac/temperature", json={"value": 30})
    assert client.get("/devices/fan/status").json()["status"] == "ON"
    assert client.delete(f"/rules/{created.json()['id']}").status_code == 204


def test_schedule_timezone_is_validated_and_returned():
    payload = {
        "device_id": "light",
        "action": "OFF",
        "time": "07:30",
        "timezone": "Europe/London",
    }
    response = client.post("/schedules", json=payload)
    assert response.status_code == 201
    assert response.json()["timezone"] == "Europe/London"
    assert client.post("/schedules", json={**payload, "timezone": "Mars/Olympus"}).status_code == 422
    assert client.delete(f"/schedules/{response.json()['id']}").status_code == 204


def test_energy_stats_and_activity_source_filter():
    stats = client.get("/energy/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert set(body) == {
        "total_wh",
        "interval_count",
        "average_interval_wh",
        "peak_device_id",
        "note",
    }

    client.post("/devices/light/off")
    api_events = client.get("/activity", params={"source": "api"}).json()["activity"]
    automation_events = client.get("/activity", params={"source": "automation"}).json()["activity"]
    assert api_events
    assert all(event["source"] == "api" for event in api_events)
    assert automation_events == []
    assert client.get("/activity", params={"source": "bogus"}).status_code == 422


def test_schedule_is_due_in_configured_timezone():
    schedule = Schedule(
        id="s-tz",
        device_id="light",
        action=PowerAction.OFF,
        time="07:30",
        timezone="America/New_York",
    )
    winter_utc = datetime(2026, 1, 5, 12, 30, tzinfo=timezone.utc)
    summer_utc = datetime(2026, 7, 6, 11, 30, tzinfo=timezone.utc)
    assert schedule.is_due(winter_utc) is True
    assert schedule.is_due(summer_utc) is True
    assert schedule.is_due(winter_utc.replace(hour=7)) is False


def test_threshold_rule_matching_boundaries():
    rule = AutomationRule(
        id="r",
        name="Above",
        trigger_device_id="ac",
        trigger_status=DeviceStatus.ON,
        target_device_id="fan",
        target_action=PowerAction.ON,
        trigger_type=TriggerType.TEMPERATURE_ABOVE,
        threshold_c=28,
    )
    assert rule.matches_temperature("ac", 28.1) is True
    assert rule.matches_temperature("ac", 28.0) is False
    assert rule.matches_temperature("fan", 30) is False
    assert rule.matches("ac", DeviceStatus.ON) is False


def test_database_mode_not_enabled_without_url():
    assert get_container().postgres is False


def test_storage_status_endpoint_reports_mode_without_secrets():
    response = client.get("/health/storage")
    assert response.status_code == 200
    assert set(response.json()) == {
        "mode",
        "database_configured",
        "automation_rules",
    }
    assert response.json()["mode"] == "memory"
    assert response.json()["database_configured"] is False


def test_switching_temperature_rule_to_device_state_clears_threshold():
    created = client.post(
        "/rules",
        json={
            "name": "Cooling threshold",
            "trigger_device_id": "ac",
            "trigger_type": "temperature_above",
            "threshold_c": 28,
            "target_device_id": "fan",
            "target_action": "ON",
        },
    )
    assert created.status_code == 201
    rule_id = created.json()["id"]

    updated = client.put(
        f"/rules/{rule_id}",
        json={
            "name": "Cooling threshold",
            "trigger_type": "device_state",
            "trigger_status": "ON",
            "target_device_id": "fan",
            "target_action": "ON",
            "threshold_c": None,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["trigger_type"] == "device_state"
    assert updated.json()["threshold_c"] is None
    assert client.get(f"/rules/{rule_id}").json()["threshold_c"] is None
