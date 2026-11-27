"""Domain entities, value objects and invariants.

This module knows nothing about HTTP, FastAPI or storage. It models the home
only: devices, rooms, schedules, rules, activity, energy and notifications.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import uuid4

try:
    from .interfaces import SmartDevice
except ImportError:
    from interfaces import SmartDevice


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid4().hex[:12]


class DeviceStatus(str, Enum):
    ON = "ON"
    OFF = "OFF"


class DeviceType(str, Enum):
    LIGHT = "light"
    FAN = "fan"
    AC = "ac"


class PowerAction(str, Enum):
    ON = "ON"
    OFF = "OFF"


class EventSource(str, Enum):
    API = "api"
    SCHEDULE = "schedule"
    AUTOMATION = "automation"
    SYSTEM = "system"


class TriggerType(str, Enum):
    DEVICE_STATE = "device_state"
    TEMPERATURE_ABOVE = "temperature_above"
    TEMPERATURE_BELOW = "temperature_below"


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class EnergyMeter:
    """Value object composed into every device.

    Consumption is accumulated from the moment a device is switched on until
    the next state change (or until a reading is requested).
    """

    wattage: float = 0.0
    total_wh: float = 0.0
    _since: datetime | None = field(default=None, repr=False)

    def mark(self, status: DeviceStatus, now: datetime | None = None) -> None:
        moment = now or utcnow()
        self.total_wh = self.reading(moment)
        self._since = moment if status is DeviceStatus.ON else None

    def reading(self, now: datetime | None = None) -> float:
        if self._since is None:
            return self.total_wh
        seconds = max(0.0, ((now or utcnow()) - self._since).total_seconds())
        return self.total_wh + self.wattage * seconds / 3600.0

    def reset(self) -> None:
        self.total_wh = 0.0
        self._since = None


class Device:
    """Base entity with encapsulated, validated state."""

    device_id: str = ""
    name: str = ""
    device_type: DeviceType = DeviceType.LIGHT

    def __init__(
        self,
        device_id: str | None = None,
        name: str | None = None,
        device_type: DeviceType | None = None,
        initial_status: str = "OFF",
        wattage: float = 0.0,
        room_id: str | None = None,
        online: bool = True,
        temperature_c: float | None = None,
    ) -> None:
        self.device_id = device_id or self.device_id
        self.name = name or self.name
        self.device_type = device_type or self.device_type
        self._status = (
            initial_status
            if isinstance(initial_status, DeviceStatus)
            else DeviceStatus(str(initial_status).upper())
        )
        self.room_id = room_id
        self.online = bool(online)
        self.temperature_c = temperature_c
        self.temperature_source = "simulated" if temperature_c is not None else None
        self.energy_meter = EnergyMeter(wattage=wattage)

    @property
    def status(self) -> str:
        return self._status.value

    @status.setter
    def status(self, value: str | DeviceStatus) -> None:
        status = value if isinstance(value, DeviceStatus) else DeviceStatus(str(value).upper())
        if status is self._status:
            return
        self._status = status
        self.energy_meter.mark(status)

    def set_online(self, online: bool) -> None:
        self.online = bool(online)

    def assign_room(self, room_id: str | None) -> None:
        self.room_id = room_id or None

    def set_temperature(self, value: float) -> None:
        self.temperature_c = round(float(value), 2)
        self.temperature_source = "simulated"

    @property
    def is_on(self) -> bool:
        return self._status is DeviceStatus.ON


class BaseDevice(Device, SmartDevice):
    """Implements the ``SmartDevice`` contract over validated ``Device`` state."""

    def turn_on(self) -> str:
        self.status = DeviceStatus.ON
        return f"{self.name} is ON"

    def turn_off(self) -> str:
        self.status = DeviceStatus.OFF
        return f"{self.name} is OFF"


@dataclass(slots=True)
class Room:
    id: str
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Room name must not be empty")


@dataclass(slots=True)
class Schedule:
    id: str
    device_id: str
    action: PowerAction
    time: str
    days: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6)
    enabled: bool = True
    last_run: datetime | None = None
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        datetime.strptime(self.time, "%H:%M")
        if not self.days or any(day < 0 or day > 6 for day in self.days):
            raise ValueError("Schedule days must contain weekday numbers 0-6")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown timezone: {self.timezone}") from exc

    def is_due(self, now: datetime | None = None) -> bool:
        moment = now or utcnow()
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        local = moment.astimezone(ZoneInfo(self.timezone))
        if not self.enabled or local.weekday() not in self.days:
            return False
        if local.strftime("%H:%M") != self.time:
            return False
        if self.last_run is not None and self.last_run.date() == local.date():
            return False
        return True


@dataclass(slots=True)
class AutomationRule:
    id: str
    name: str
    trigger_device_id: str
    trigger_status: DeviceStatus
    target_device_id: str
    target_action: PowerAction
    enabled: bool = True
    trigger_type: TriggerType = TriggerType.DEVICE_STATE
    threshold_c: float | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Automation rule name must not be empty")
        if isinstance(self.trigger_type, str):
            self.trigger_type = TriggerType(self.trigger_type)
        if self.trigger_type in (
            TriggerType.TEMPERATURE_ABOVE,
            TriggerType.TEMPERATURE_BELOW,
        ) and self.threshold_c is None:
            raise ValueError("Temperature rules require a threshold_c value")

    def matches(self, device_id: str, status: DeviceStatus) -> bool:
        return (
            self.enabled
            and self.trigger_type is TriggerType.DEVICE_STATE
            and self.trigger_device_id == device_id
            and self.trigger_status is status
        )

    def matches_temperature(self, device_id: str, value: float) -> bool:
        if not self.enabled or self.trigger_device_id != device_id:
            return False
        if self.trigger_type is TriggerType.TEMPERATURE_ABOVE:
            return value > self.threshold_c
        if self.trigger_type is TriggerType.TEMPERATURE_BELOW:
            return value < self.threshold_c
        return False


@dataclass(slots=True)
class ActivityEvent:
    id: str
    device_id: str
    action: str
    previous_status: str
    status: str
    source: EventSource
    occurred_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class EnergyLog:
    """One estimated consumption interval, derived from power and on-time."""

    device_id: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    wattage: float
    estimated_energy_wh: float
    id: int | None = None
    measurement_source: str = "estimated"


@dataclass(slots=True)
class Notification:
    id: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    read: bool = False
    created_at: datetime = field(default_factory=utcnow)

    def mark_read(self) -> None:
        self.read = True
