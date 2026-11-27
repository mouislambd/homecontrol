import pytest
from datetime import datetime, timedelta, timezone

from backend.domain import (
    Device,
    DeviceStatus,
    DeviceType,
    EnergyMeter,
    PowerAction,
    Schedule,
)
from backend.events import DomainEvent, InMemoryEventPublisher
from backend.exceptions import (
    ConflictError,
    DeviceNotFoundError,
    DeviceOfflineError,
)
from backend.interfaces import Repository, SmartDevice
from backend.repositories import InMemoryRepository
from backend.services import DeviceService
from backend.devices import Light


def test_device_rejects_invalid_initial_status():
    with pytest.raises(ValueError):
        Light("BROKEN")


def test_device_status_setter_validates_and_is_idempotent():
    class RecordingMeter:
        def __init__(self) -> None:
            self.marks = []

        def mark(self, status, now=None) -> None:
            self.marks.append(status)

    device = Device("x", "Test", DeviceType.LIGHT)
    meter = RecordingMeter()
    device.energy_meter = meter

    device.status = "ON"
    device.status = DeviceStatus.ON

    assert device.status == "ON"
    assert device.is_on is True
    assert meter.marks == [DeviceStatus.ON]
    with pytest.raises(ValueError):
        device.status = "UNKNOWN"


def test_energy_meter_only_accumulates_while_on():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    meter = EnergyMeter(wattage=100)
    meter.mark(DeviceStatus.ON, start)

    assert meter.reading(start + timedelta(hours=1)) == pytest.approx(100)

    meter.mark(DeviceStatus.OFF, start + timedelta(hours=1))
    assert meter.reading(start + timedelta(hours=2)) == pytest.approx(100)


def test_device_composes_energy_meter():
    device = Device("x", "Test", DeviceType.AC, wattage=1200)
    assert isinstance(device.energy_meter, EnergyMeter)
    assert device.energy_meter.wattage == 1200


def test_repository_returns_immutable_snapshot_and_rejects_duplicates():
    device = Light()
    repo = InMemoryRepository(key=lambda item: item.device_id, items=[device])

    snapshot = repo.get_all()
    assert snapshot == (device,)
    assert isinstance(snapshot, tuple)
    assert repo.get("light") is device
    with pytest.raises(ConflictError):
        repo.add(Light())


def test_repository_is_isolated_between_instances():
    first = InMemoryRepository(key=lambda item: item.device_id, items=[Light()])
    second = InMemoryRepository(key=lambda item: item.device_id)
    assert len(first) == 1
    assert len(second) == 0


def test_device_service_uses_injected_repository():
    repo = InMemoryRepository(key=lambda item: item.device_id, items=[Light()])
    assert isinstance(repo, Repository)
    service = DeviceService(repo)

    assert [device.device_id for device in service.list_devices()] == ["light"]


def test_device_service_publishes_state_event():
    events = InMemoryEventPublisher()
    service = DeviceService(
        InMemoryRepository(key=lambda item: item.device_id, items=[Light()]),
        events,
    )

    result = service.set_power("light", True)

    assert result.message == "Light is ON"
    assert len(events.events) == 1
    event = events.events[0]
    assert isinstance(event, DomainEvent)
    assert event.topic == "device.state_changed"
    assert event.payload["status"] == "ON"
    assert event.payload["previous_status"] == "OFF"


def test_device_service_rejects_missing_and_offline_devices():
    offline = Light()
    offline.set_online(False)
    service = DeviceService(
        InMemoryRepository(key=lambda item: item.device_id, items=[offline])
    )

    with pytest.raises(DeviceOfflineError):
        service.set_power("light", True)
    with pytest.raises(DeviceNotFoundError, match="Device 'missing' not found"):
        service.set_power("missing", True)


def test_schedule_validates_time_and_weekdays():
    schedule = Schedule(
        id="s1",
        device_id="light",
        action=PowerAction.ON,
        time="07:30",
        days=(0, 6),
    )
    moment = datetime(2026, 1, 5, 7, 30, tzinfo=timezone.utc)
    assert schedule.is_due(moment) is True
    assert schedule.is_due(moment + timedelta(minutes=1)) is False

    with pytest.raises(ValueError):
        Schedule("s2", "light", PowerAction.ON, "25:00")
    with pytest.raises(ValueError):
        Schedule("s3", "light", PowerAction.ON, "07:00", days=(9,))


def test_all_concrete_devices_satisfy_the_interface():
    from backend.devices import AC, Fan

    for device in (Light(), Fan(), AC()):
        assert isinstance(device, SmartDevice)


def test_offline_device_can_be_brought_back_online():
    device = Light()
    service = DeviceService(
        InMemoryRepository(key=lambda item: item.device_id, items=[device])
    )
    service.set_online("light", False)
    with pytest.raises(DeviceOfflineError):
        service.set_power("light", True)
    service.set_online("light", True)
    assert service.set_power("light", True).device.status == "ON"
