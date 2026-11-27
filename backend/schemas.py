"""Pydantic request/response models and validation at the HTTP boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PowerValue = Literal["ON", "OFF"]
TriggerValue = Literal["device_state", "temperature_above", "temperature_below"]


def valid_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone must be a valid IANA name") from exc
    return value


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=200)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Room name must not be blank")
        return value.strip()


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=200)


class RoomOut(BaseModel):
    id: str
    name: str
    description: str
    device_count: int = 0


class RoomList(BaseModel):
    rooms: list[RoomOut]


class DeviceDetail(BaseModel):
    id: str
    name: str
    status: PowerValue
    device_type: str
    online: bool
    room_id: str | None
    wattage: float
    energy_wh: float
    temperature_c: float | None = None
    temperature_source: str | None = None


class TemperatureUpdate(BaseModel):
    value: float = Field(ge=-100, le=200)


class RoomAssignment(BaseModel):
    room_id: str | None


class DeviceCreate(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=80)
    device_type: Literal["light", "fan", "ac"]
    wattage: float = Field(default=0, ge=0, le=100000)
    room_id: str | None = None
    online: bool = True
    initial_status: PowerValue = "OFF"

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Device name must not be blank")
        return value.strip()


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    wattage: float | None = Field(default=None, ge=0, le=100000)
    room_id: str | None = None
    online: bool | None = None


class ScheduleCreate(BaseModel):
    device_id: str = Field(min_length=1)
    action: PowerValue
    time: str
    days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    enabled: bool = True
    timezone: str = "UTC"

    @field_validator("time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        from datetime import datetime as _datetime

        try:
            _datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("time must use HH:MM format") from exc
        return value

    @field_validator("days")
    @classmethod
    def valid_days(cls, value: list[int]) -> list[int]:
        if not value or any(day < 0 or day > 6 for day in value):
            raise ValueError("days must contain weekday numbers 0-6")
        return sorted(set(value))

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return valid_timezone(value)


class ScheduleUpdate(BaseModel):
    device_id: str | None = None
    action: PowerValue | None = None
    time: str | None = None
    days: list[int] | None = None
    enabled: bool | None = None
    timezone: str | None = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str | None) -> str | None:
        return valid_timezone(value) if value is not None else None

    @field_validator("time")
    @classmethod
    def valid_time(cls, value: str | None) -> str | None:
        if value is None:
            return None
        from datetime import datetime as _datetime

        try:
            _datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("time must use HH:MM format") from exc
        return value

    @field_validator("days")
    @classmethod
    def valid_days(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if not value or any(day < 0 or day > 6 for day in value):
            raise ValueError("days must contain weekday numbers 0-6")
        return sorted(set(value))


class ScheduleOut(BaseModel):
    id: str
    device_id: str
    action: PowerValue
    time: str
    days: list[int]
    enabled: bool
    timezone: str
    last_run: datetime | None


class ScheduleList(BaseModel):
    schedules: list[ScheduleOut]


class RuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    trigger_device_id: str
    trigger_status: PowerValue = "ON"
    target_device_id: str
    target_action: PowerValue
    enabled: bool = True
    trigger_type: TriggerValue = "device_state"
    threshold_c: float | None = Field(default=None, ge=-100, le=200)

    @model_validator(mode="after")
    def threshold_required_for_temperature(self):
        if (
            self.trigger_type in ("temperature_above", "temperature_below")
            and self.threshold_c is None
        ):
            raise ValueError("threshold_c is required for temperature rules")
        return self

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Automation rule name must not be blank")
        return value.strip()


class RuleUpdate(BaseModel):
    name: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("Automation rule name must not be blank")
        return value.strip()
    trigger_device_id: str | None = None
    trigger_status: PowerValue | None = None
    target_device_id: str | None = None
    target_action: PowerValue | None = None
    enabled: bool | None = None
    trigger_type: TriggerValue | None = None
    threshold_c: float | None = Field(default=None, ge=-100, le=200)


class RuleOut(BaseModel):
    id: str
    name: str
    trigger_device_id: str
    trigger_status: PowerValue
    target_device_id: str
    target_action: PowerValue
    enabled: bool
    trigger_type: TriggerValue
    threshold_c: float | None


class RuleList(BaseModel):
    rules: list[RuleOut]


class ActivityOut(BaseModel):
    id: str
    device_id: str
    action: str
    previous_status: str
    status: str
    source: str
    occurred_at: datetime


class ActivityList(BaseModel):
    activity: list[ActivityOut]


class NotificationOut(BaseModel):
    id: str
    message: str
    level: str
    read: bool
    created_at: datetime


class NotificationList(BaseModel):
    notifications: list[NotificationOut]
    unread_count: int


class EnergyDeviceOut(BaseModel):
    device_id: str
    name: str
    wattage: float
    energy_wh: float


class EnergySummary(BaseModel):
    total_wh: float
    devices: list[EnergyDeviceOut]


class EnergyLogOut(BaseModel):
    id: int
    device_id: str
    started_at: datetime
    ended_at: datetime
    duration_seconds: float
    wattage: float
    estimated_energy_wh: float
    measurement_source: Literal["estimated"]


class EnergyLogList(BaseModel):
    logs: list[EnergyLogOut]
    note: str = (
        "Estimated values derived from rated power and on-time; "
        "no physical energy meter is attached."
    )


class EnergyStats(BaseModel):
    total_wh: float
    interval_count: int
    average_interval_wh: float
    peak_device_id: str | None
    note: str = "Estimated values; no physical energy meter is attached."
