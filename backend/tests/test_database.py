import time
from datetime import datetime, timezone

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from backend.container import AppContainer
from backend.database import dispose_engine, get_engine, session_scope
from backend.db_repositories import DEMO_USER_ID, _as_uuid
from backend.domain import DeviceStatus, DeviceType, PowerAction, TriggerType
from backend.models import (
    AutomationModel,
    Base,
    DeviceHistoryModel,
    DeviceModel,
    EnergyLogModel,
    NotificationModel,
    RoomModel,
    ScheduleDayModel,
    ScheduleModel,
    UserModel,
)
from backend.seed import seed_demo_data


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    path = tmp_path / "smart_home_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path.as_posix()}")
    dispose_engine()
    engine = get_engine()

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    seed_demo_data()
    yield engine
    dispose_engine()


def test_schema_contains_all_expected_tables(db_env):
    assert set(Base.metadata.tables) == {
        "users",
        "rooms",
        "room_members",
        "devices",
        "device_history",
        "energy_logs",
        "schedules",
        "schedule_days",
        "automations",
        "notifications",
    }
    assert any(c.name == "ck_devices_status" for c in DeviceModel.__table__.constraints)
    assert any(c.name == "ck_energy_source_estimated" for c in EnergyLogModel.__table__.constraints)


def test_seed_populates_owner_rooms_and_devices(db_env):
    with session_scope() as session:
        user = session.get(UserModel, DEMO_USER_ID)
        assert user.display_name == "Demo User"
        assert sorted(room.id for room in user.rooms) == ["bedroom", "living-room"]
        assert sorted(device.id for device in user.devices) == ["ac", "fan", "light"]

    container = AppContainer(postgres=True)
    devices = {device.device_id: device for device in container.device_service.list_devices()}
    assert devices["light"].name == "Light"
    assert devices["ac"].energy_meter.wattage == 1200.0
    assert devices["fan"].room_id == "bedroom"


def test_repository_crud_round_trip(db_env):
    container = AppContainer(postgres=True)
    device = container.device_service.create_device(
        "plug", "Smart Plug", DeviceType.LIGHT, 25.0, room_id="living-room"
    )

    assert container.device_service.get_device("plug").name == "Smart Plug"
    assert len(container.device_service.list_devices()) == 4

    updated = container.device_service.update_device("plug", name="Desk Lamp", wattage=40.0)
    assert updated.name == "Desk Lamp"
    assert container.device_service.get_device("plug").energy_meter.wattage == 40.0

    container.device_service.delete_device("plug")
    with pytest.raises(Exception):
        container.device_service.get_device("plug")


def test_schedule_days_are_normalized(db_env):
    container = AppContainer(postgres=True)
    schedule = container.schedule_service.create_schedule(
        "light", PowerAction.ON, "07:30", (0, 6)
    )
    loaded = container.schedule_service.get_schedule(schedule.id)

    assert set(loaded.days) == {0, 6}
    with session_scope() as session:
        rows = session.scalars(
            select(ScheduleDayModel).where(ScheduleDayModel.schedule_id == _as_uuid(schedule.id))
        ).all()
        assert sorted(row.day for row in rows) == [0, 6]


def test_automation_two_device_foreign_keys(db_env):
    container = AppContainer(postgres=True)
    rule = container.automation_service.create_rule(
        "Light starts fan", "light", DeviceStatus.ON, "fan", PowerAction.ON
    )
    with session_scope() as session:
        row = session.get(AutomationModel, _as_uuid(rule.id))
        assert row.trigger_device.name == "Light"
        assert row.target_device.name == "Fan"


def test_power_change_writes_history_notification_and_energy_log(db_env):
    container = AppContainer(postgres=True)
    container.device_service.set_power("fan", True)
    time.sleep(0.01)
    container.device_service.set_power("fan", False)

    logs = container.energy_service.logs("fan", 10)
    assert len(logs) == 1
    assert logs[0].measurement_source == "estimated"
    assert logs[0].estimated_energy_wh >= 0

    activity = container.activity_service.list_events("fan", 10)
    assert {event.action for event in activity} == {"ON", "OFF"}
    assert all(event.source.value == "api" for event in activity)
    assert container.notification_service.unread_count >= 2


def test_new_fields_persist_in_database(db_env):
    container = AppContainer(postgres=True)
    container.device_service.set_temperature("ac", 31.5)
    schedule = container.schedule_service.create_schedule(
        "light", PowerAction.OFF, "07:30", (0,), timezone_name="Asia/Kolkata"
    )
    rule = container.automation_service.create_rule(
        "Hot room",
        "ac",
        DeviceStatus.ON,
        "fan",
        PowerAction.ON,
        trigger_type=TriggerType.TEMPERATURE_ABOVE,
        threshold_c=29.0,
    )

    with session_scope() as session:
        device = session.get(DeviceModel, "ac")
        assert float(device.temperature_c) == 31.5
        assert device.temperature_source == "simulated"

        schedule_row = session.get(ScheduleModel, _as_uuid(schedule.id))
        assert schedule_row.timezone == "Asia/Kolkata"

        rule_row = session.get(AutomationModel, _as_uuid(rule.id))
        assert rule_row.trigger_type == "temperature_above"
        assert float(rule_row.threshold_c) == 29.0


def test_threshold_automation_works_with_database(db_env):
    container = AppContainer(postgres=True)
    container.automation_service.create_rule(
        "Hot AC starts fan",
        "ac",
        DeviceStatus.ON,
        "fan",
        PowerAction.ON,
        trigger_type=TriggerType.TEMPERATURE_ABOVE,
        threshold_c=28,
    )
    container.device_service.set_temperature("ac", 30)
    assert container.device_service.get_device("fan").status == "ON"
    assert any(
        event.source.value == "automation"
        for event in container.activity_service.list_events("fan", 10)
    )


def test_timezone_schedule_due_with_database(db_env):
    container = AppContainer(postgres=True)
    schedule = container.schedule_service.create_schedule(
        "light", PowerAction.OFF, "07:30", (0,), timezone_name="America/New_York"
    )
    fired = container.schedule_service.run_due(
        datetime(2026, 1, 5, 12, 30, tzinfo=timezone.utc)
    )
    assert [item.id for item in fired] == [schedule.id]
    assert container.device_service.get_device("light").status == "OFF"


def test_temperature_rule_survives_container_reload_and_crud(db_env):
    first = AppContainer(postgres=True)
    created = first.automation_service.create_rule(
        "Hot room persistence",
        "ac",
        DeviceStatus.ON,
        "fan",
        PowerAction.ON,
        trigger_type=TriggerType.TEMPERATURE_ABOVE,
        threshold_c=29.0,
    )
    first.automation_service.update_rule(
        created.id, name="Hot room updated", threshold_c=30.0
    )

    reloaded = AppContainer(postgres=True)
    rules = reloaded.automation_service.list_rules()
    assert len(rules) == 1
    assert rules[0].name == "Hot room updated"
    assert rules[0].trigger_type is TriggerType.TEMPERATURE_ABOVE
    assert rules[0].threshold_c == 30.0

    reloaded.automation_service.update_rule(
        rules[0].id,
        trigger_type=TriggerType.DEVICE_STATE,
        clear_threshold=True,
    )
    after_clear = AppContainer(postgres=True).automation_service.get_rule(rules[0].id)
    assert after_clear.trigger_type is TriggerType.DEVICE_STATE
    assert after_clear.threshold_c is None

    reloaded.automation_service.delete_rule(rules[0].id)
    assert AppContainer(postgres=True).automation_service.list_rules() == ()


def test_database_constraints_are_enforced(db_env):
    with pytest.raises(IntegrityError):
        with session_scope() as session:
            session.add(
                EnergyLogModel(
                    device_id="light",
                    started_at=datetime.now(timezone.utc),
                    ended_at=datetime.now(timezone.utc),
                    duration_seconds=1,
                    wattage=10,
                    estimated_energy_wh=1,
                    measurement_source="measured",
                )
            )

    with pytest.raises(IntegrityError):
        with session_scope() as session:
            session.add(
                RoomModel(id="dup", owner_user_id=DEMO_USER_ID, name="Living Room")
            )


def test_deleting_device_cascades_to_child_rows(db_env):
    container = AppContainer(postgres=True)
    container.device_service.set_power("fan", True)
    time.sleep(0.01)
    container.device_service.set_power("fan", False)

    with session_scope() as session:
        assert session.scalar(
            select(func.count()).select_from(DeviceHistoryModel).where(DeviceHistoryModel.device_id == "fan")
        ) > 0
        session.delete(session.get(DeviceModel, "fan"))

    with session_scope() as session:
        assert session.scalar(
            select(func.count()).select_from(DeviceHistoryModel).where(DeviceHistoryModel.device_id == "fan")
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(EnergyLogModel).where(EnergyLogModel.device_id == "fan")
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(ScheduleModel).where(ScheduleModel.device_id == "fan")
        ) == 0
        assert session.scalar(
            select(func.count()).select_from(NotificationModel)
        ) > 0
