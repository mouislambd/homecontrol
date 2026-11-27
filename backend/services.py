"""Application services: the use-case layer, independent of HTTP and storage."""

import logging
from collections.abc import Callable
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime

try:
    from .controller import control_device
    from .domain import (
        ActivityEvent,
        AutomationRule,
        BaseDevice,
        DeviceStatus,
        DeviceType,
        EnergyLog,
        EventSource,
        Notification,
        NotificationLevel,
        PowerAction,
        Room,
        Schedule,
        TriggerType,
        new_id,
        utcnow,
    )
    from .events import DomainEvent, NoopEventPublisher
    from .exceptions import (
        ConflictError,
        DeviceNotFoundError,
        DeviceOfflineError,
        NotificationNotFoundError,
        RoomNotFoundError,
        RuleNotFoundError,
        ScheduleNotFoundError,
        SmartHomeError,
    )
    from .interfaces import EventPublisher, Repository, SmartDevice
except ImportError:
    from controller import control_device
    from domain import (
        ActivityEvent,
        AutomationRule,
        BaseDevice,
        DeviceStatus,
        DeviceType,
        EnergyLog,
        EventSource,
        Notification,
        NotificationLevel,
        PowerAction,
        Room,
        Schedule,
        TriggerType,
        new_id,
        utcnow,
    )
    from events import DomainEvent, NoopEventPublisher
    from exceptions import (
        ConflictError,
        DeviceNotFoundError,
        DeviceOfflineError,
        NotificationNotFoundError,
        RoomNotFoundError,
        RuleNotFoundError,
        ScheduleNotFoundError,
        SmartHomeError,
    )
    from interfaces import EventPublisher, Repository, SmartDevice

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PowerResult:
    device: SmartDevice
    message: str


@dataclass(frozen=True)
class EnergyReading:
    device_id: str
    name: str
    wattage: float
    energy_wh: float


class DeviceService:
    """Device use cases, depending only on abstractions (DIP)."""

    def __init__(
        self,
        repository: Repository[SmartDevice],
        events: EventPublisher | None = None,
        energy_logs=None,
        transaction=None,
    ) -> None:
        self._repository = repository
        self._events = events or NoopEventPublisher()
        self._energy_logs = energy_logs
        self._transaction = transaction or (lambda: nullcontext())

    def list_devices(self) -> tuple[SmartDevice, ...]:
        return self._repository.get_all()

    def get_device(self, device_id: str) -> SmartDevice:
        device = self._repository.get(device_id)
        if device is None:
            raise DeviceNotFoundError.for_id(device_id)
        return device

    def set_power(
        self,
        device_id: str,
        should_turn_on: bool,
        source: EventSource = EventSource.API,
    ) -> PowerResult:
        with self._transaction():
            device = self.get_device(device_id)
            if not device.online:
                raise DeviceOfflineError.for_id(device_id)

            previous = device.status
            started_at = device.energy_meter._since
            message = control_device(device, should_turn_on)
            logger.info(
                "device power changed: id=%s from=%s to=%s source=%s",
                device_id,
                previous,
                device.status,
                source.value,
            )

            if (
                previous == "ON"
                and device.status == "OFF"
                and self._energy_logs is not None
                and started_at is not None
            ):
                ended_at = utcnow()
                duration = max(0.0, (ended_at - started_at).total_seconds())
                if duration > 0:
                    wattage = device.energy_meter.wattage
                    self._energy_logs.add(
                        EnergyLog(
                            device_id=device_id,
                            started_at=started_at,
                            ended_at=ended_at,
                            duration_seconds=duration,
                            wattage=wattage,
                            estimated_energy_wh=wattage * duration / 3600.0,
                        )
                    )

            self._repository.update(device)
            self._events.publish(
                DomainEvent(
                    topic="device.state_changed",
                    payload={
                        "device_id": device_id,
                        "previous_status": previous,
                        "status": device.status,
                        "source": source.value,
                    },
                )
            )
        return PowerResult(device=device, message=message)

    def set_online(self, device_id: str, online: bool) -> SmartDevice:
        device = self.get_device(device_id)
        device.set_online(online)
        self._repository.update(device)
        logger.info("device connectivity changed: id=%s online=%s", device_id, online)
        self._events.publish(
            DomainEvent(
                topic="device.connectivity_changed",
                payload={"device_id": device_id, "online": online},
            )
        )
        return device

    def set_temperature(self, device_id: str, value: float) -> SmartDevice:
        with self._transaction():
            device = self.get_device(device_id)
            device.set_temperature(value)
            self._repository.update(device)
            logger.info("device temperature input: id=%s value=%s (simulated)", device_id, value)
            self._events.publish(
                DomainEvent(
                    "device.temperature_changed",
                    {"device_id": device_id, "temperature_c": device.temperature_c},
                )
            )
            return device

    def create_device(
        self,
        device_id: str,
        name: str,
        device_type: DeviceType,
        wattage: float,
        room_id: str | None = None,
        online: bool = True,
        initial_status: DeviceStatus = DeviceStatus.OFF,
    ) -> SmartDevice:
        with self._transaction():
            if self._repository.get(device_id) is not None:
                raise ConflictError(f"Device '{device_id}' already exists")
            device = BaseDevice(
                device_id,
                name.strip(),
                DeviceType(device_type),
                initial_status,
                wattage=wattage,
                room_id=room_id,
                online=online,
            )
            self._repository.add(device)
            self._events.publish(
                DomainEvent(
                    "device.created",
                    {"device_id": device_id, "name": device.name},
                )
            )
            return device

    def update_device(
        self,
        device_id: str,
        name: str | None = None,
        wattage: float | None = None,
        room_id: str | None = None,
        online: bool | None = None,
    ) -> SmartDevice:
        with self._transaction():
            device = self.get_device(device_id)
            if name is not None:
                device.name = name.strip()
            if wattage is not None:
                device.energy_meter.wattage = wattage
            if room_id is not None:
                device.assign_room(room_id)
            if online is not None:
                device.set_online(online)
            self._repository.update(device)
            self._events.publish(
                DomainEvent("device.updated", {"device_id": device_id})
            )
            return device

    def delete_device(self, device_id: str) -> SmartDevice:
        with self._transaction():
            device = self.get_device(device_id)
            self._repository.remove(device_id)
            self._events.publish(
                DomainEvent("device.deleted", {"device_id": device_id})
            )
            return device


class EnergyService:
    """Reads accumulated consumption composed into each device."""

    def __init__(self, devices: Repository[SmartDevice], energy_logs=None) -> None:
        self._devices = devices
        self._energy_logs = energy_logs

    def logs(self, device_id: str | None = None, limit: int = 100) -> tuple[EnergyLog, ...]:
        if self._energy_logs is None:
            return ()
        return self._energy_logs.logs_for(device_id, limit)

    def readings(self) -> tuple[EnergyReading, ...]:
        return tuple(
            EnergyReading(
                device_id=device.device_id,
                name=device.name,
                wattage=device.energy_meter.wattage,
                energy_wh=round(device.energy_meter.reading(), 4),
            )
            for device in self._devices.get_all()
        )

    def reading_for(self, device_id: str) -> EnergyReading:
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceNotFoundError.for_id(device_id)
        return EnergyReading(
            device_id=device.device_id,
            name=device.name,
            wattage=device.energy_meter.wattage,
            energy_wh=round(device.energy_meter.reading(), 4),
        )

    def total_wh(self) -> float:
        return round(sum(item.energy_wh for item in self.readings()), 4)


class RoomService:
    def __init__(
        self,
        rooms: Repository[Room],
        devices: Repository[SmartDevice],
        events: EventPublisher,
    ) -> None:
        self._rooms = rooms
        self._devices = devices
        self._events = events

    def list_rooms(self) -> tuple[Room, ...]:
        return self._rooms.get_all()

    def get_room(self, room_id: str) -> Room:
        room = self._rooms.get(room_id)
        if room is None:
            raise RoomNotFoundError.for_id(room_id)
        return room

    def create_room(self, name: str, description: str = "") -> Room:
        if any(room.name.lower() == name.lower() for room in self._rooms.get_all()):
            raise ConflictError(f"Room '{name}' already exists")
        room = Room(id=new_id(), name=name.strip(), description=description.strip())
        self._rooms.add(room)
        logger.info("room created: id=%s name=%s", room.id, room.name)
        self._events.publish(
            DomainEvent("room.created", {"room_id": room.id, "name": room.name})
        )
        return room

    def update_room(self, room_id: str, name: str | None, description: str | None) -> Room:
        room = self.get_room(room_id)
        if name is not None:
            if name.strip().lower() != room.name.lower() and any(
                other.name.lower() == name.strip().lower()
                for other in self._rooms.get_all()
                if other.id != room_id
            ):
                raise ConflictError(f"Room '{name}' already exists")
            room.name = name.strip()
        if description is not None:
            room.description = description.strip()
        self._rooms.update(room)
        return room

    def delete_room(self, room_id: str) -> Room:
        room = self.get_room(room_id)
        for device in self._devices.get_all():
            if device.room_id == room_id:
                device.assign_room(None)
                self._devices.update(device)
        self._rooms.remove(room_id)
        self._events.publish(DomainEvent("room.deleted", {"room_id": room_id}))
        return room

    def assign_device(self, device_id: str, room_id: str | None) -> SmartDevice:
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceNotFoundError.for_id(device_id)
        if room_id is not None:
            self.get_room(room_id)
        device.assign_room(room_id)
        self._devices.update(device)
        self._events.publish(
            DomainEvent(
                "device.room_changed",
                {"device_id": device_id, "room_id": room_id},
            )
        )
        return device

    def devices_in(self, room_id: str) -> tuple[SmartDevice, ...]:
        self.get_room(room_id)
        return tuple(d for d in self._devices.get_all() if d.room_id == room_id)


class ScheduleService:
    def __init__(
        self,
        schedules: Repository[Schedule],
        device_service: DeviceService,
        events: EventPublisher,
    ) -> None:
        self._schedules = schedules
        self._devices = device_service
        self._events = events

    def list_schedules(self) -> tuple[Schedule, ...]:
        return self._schedules.get_all()

    def get_schedule(self, schedule_id: str) -> Schedule:
        schedule = self._schedules.get(schedule_id)
        if schedule is None:
            raise ScheduleNotFoundError.for_id(schedule_id)
        return schedule

    def create_schedule(
        self,
        device_id: str,
        action: PowerAction,
        time: str,
        days: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6),
        enabled: bool = True,
        timezone_name: str = "UTC",
    ) -> Schedule:
        self._devices.get_device(device_id)
        schedule = Schedule(
            id=new_id(),
            device_id=device_id,
            action=PowerAction(action),
            time=time,
            days=tuple(sorted(set(days))),
            enabled=enabled,
            timezone=timezone_name,
        )
        self._schedules.add(schedule)
        return schedule

    def update_schedule(
        self,
        schedule_id: str,
        device_id: str | None = None,
        action: PowerAction | None = None,
        time: str | None = None,
        days: tuple[int, ...] | None = None,
        enabled: bool | None = None,
        timezone_name: str | None = None,
    ) -> Schedule:
        schedule = self.get_schedule(schedule_id)
        if device_id is not None:
            self._devices.get_device(device_id)
            schedule.device_id = device_id
        if action is not None:
            schedule.action = PowerAction(action)
        if time is not None:
            schedule.time = time
        if days is not None:
            schedule.days = tuple(sorted(set(days)))
        if enabled is not None:
            schedule.enabled = enabled
        if timezone_name is not None:
            schedule.timezone = timezone_name
        self._schedules.update(schedule)
        return schedule

    def delete_schedule(self, schedule_id: str) -> Schedule:
        schedule = self.get_schedule(schedule_id)
        self._schedules.remove(schedule_id)
        return schedule

    def run_due(self, now: datetime | None = None) -> tuple[Schedule, ...]:
        moment = now or utcnow()
        fired: list[Schedule] = []
        for schedule in self._schedules.get_all():
            if not schedule.is_due(moment):
                continue
            try:
                self._devices.set_power(
                    schedule.device_id,
                    schedule.action is PowerAction.ON,
                    source=EventSource.SCHEDULE,
                )
            except SmartHomeError as exc:
                self._events.publish(
                    DomainEvent(
                        "schedule.failed",
                        {"schedule_id": schedule.id, "reason": exc.message},
                    )
                )
                continue
            schedule.last_run = moment
            self._schedules.update(schedule)
            self._events.publish(
                DomainEvent("schedule.fired", {"schedule_id": schedule.id})
            )
            fired.append(schedule)
        return tuple(fired)


class AutomationService:
    """Event-driven rule engine with a guard against cascading chains."""

    def __init__(
        self,
        rules: Repository[AutomationRule],
        device_service: DeviceService,
        events: EventPublisher,
    ) -> None:
        self._rules = rules
        self._devices = device_service
        self._events = events
        self._handling = False

    def list_rules(self) -> tuple[AutomationRule, ...]:
        return self._rules.get_all()

    def get_rule(self, rule_id: str) -> AutomationRule:
        rule = self._rules.get(rule_id)
        if rule is None:
            raise RuleNotFoundError.for_id(rule_id)
        return rule

    def create_rule(
        self,
        name: str,
        trigger_device_id: str,
        trigger_status: DeviceStatus,
        target_device_id: str,
        target_action: PowerAction,
        enabled: bool = True,
        trigger_type: TriggerType = TriggerType.DEVICE_STATE,
        threshold_c: float | None = None,
    ) -> AutomationRule:
        self._devices.get_device(trigger_device_id)
        self._devices.get_device(target_device_id)
        rule = AutomationRule(
            id=new_id(),
            name=name.strip(),
            trigger_device_id=trigger_device_id,
            trigger_status=DeviceStatus(trigger_status),
            target_device_id=target_device_id,
            target_action=PowerAction(target_action),
            enabled=enabled,
            trigger_type=TriggerType(trigger_type),
            threshold_c=threshold_c,
        )
        self._rules.add(rule)
        return rule

    def update_rule(
        self,
        rule_id: str,
        name: str | None = None,
        trigger_device_id: str | None = None,
        trigger_status: DeviceStatus | None = None,
        target_device_id: str | None = None,
        target_action: PowerAction | None = None,
        enabled: bool | None = None,
        trigger_type: TriggerType | None = None,
        threshold_c: float | None = None,
    ) -> AutomationRule:
        rule = self.get_rule(rule_id)
        if trigger_device_id is not None:
            self._devices.get_device(trigger_device_id)
            rule.trigger_device_id = trigger_device_id
        if target_device_id is not None:
            self._devices.get_device(target_device_id)
            rule.target_device_id = target_device_id
        if name is not None:
            rule.name = name.strip()
        if trigger_status is not None:
            rule.trigger_status = DeviceStatus(trigger_status)
        if target_action is not None:
            rule.target_action = PowerAction(target_action)
        if enabled is not None:
            rule.enabled = enabled
        if trigger_type is not None:
            rule.trigger_type = TriggerType(trigger_type)
        if threshold_c is not None:
            rule.threshold_c = threshold_c
        self._rules.update(rule)
        return rule

    def delete_rule(self, rule_id: str) -> AutomationRule:
        rule = self.get_rule(rule_id)
        self._rules.remove(rule_id)
        return rule

    def on_device_state_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        device_id = payload["device_id"]
        status = DeviceStatus(payload["status"])
        self._apply_rules(lambda rule: rule.matches(device_id, status))

    def on_temperature_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        device_id = payload["device_id"]
        value = float(payload["temperature_c"])
        self._apply_rules(lambda rule: rule.matches_temperature(device_id, value))

    def _apply_rules(self, predicate: Callable[[AutomationRule], bool]) -> None:
        if self._handling:
            return
        self._handling = True
        try:
            for rule in self._rules.get_all():
                if not predicate(rule):
                    continue
                try:
                    self._devices.set_power(
                        rule.target_device_id,
                        rule.target_action is PowerAction.ON,
                        source=EventSource.AUTOMATION,
                    )
                except SmartHomeError as exc:
                    self._events.publish(
                        DomainEvent(
                            "automation.failed",
                            {"rule_id": rule.id, "reason": exc.message},
                        )
                    )
                    continue
                self._events.publish(
                    DomainEvent(
                        "automation.triggered",
                        {"rule_id": rule.id, "name": rule.name},
                    )
                )
        finally:
            self._handling = False


class ActivityService:
    """Appends an immutable audit record for every state/connectivity change."""

    def __init__(self, activity: Repository[ActivityEvent]) -> None:
        self._activity = activity

    def on_device_state_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        self._activity.add(
            ActivityEvent(
                id=new_id(),
                device_id=payload["device_id"],
                action=payload["status"],
                previous_status=payload["previous_status"],
                status=payload["status"],
                source=EventSource(payload["source"]),
                occurred_at=event.occurred_at,
            )
        )

    def on_connectivity_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        online = bool(payload["online"])
        value = "ONLINE" if online else "OFFLINE"
        self._activity.add(
            ActivityEvent(
                id=new_id(),
                device_id=payload["device_id"],
                action=value,
                previous_status="OFFLINE" if online else "ONLINE",
                status=value,
                source=EventSource.SYSTEM,
                occurred_at=event.occurred_at,
            )
        )

    def on_temperature_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        value = f"{float(payload['temperature_c']):.1f}"
        self._activity.add(
            ActivityEvent(
                id=new_id(),
                device_id=payload["device_id"],
                action="TEMPERATURE",
                previous_status="",
                status=value,
                source=EventSource.SYSTEM,
                occurred_at=event.occurred_at,
            )
        )

    def list_events(
        self,
        device_id: str | None = None,
        limit: int = 100,
        source: str | None = None,
    ) -> tuple[ActivityEvent, ...]:
        items = reversed(self._activity.get_all())
        if device_id is not None:
            items = (item for item in items if item.device_id == device_id)
        if source is not None:
            items = (item for item in items if item.source.value == source)
        return tuple(list(items)[: max(0, min(limit, 500))])


class NotificationService:
    """Turns domain events into notifications for the dashboard."""

    def __init__(self, notifications: Repository[Notification]) -> None:
        self._notifications = notifications

    def _add(self, message: str, level: NotificationLevel) -> None:
        self._notifications.add(
            Notification(id=new_id(), message=message, level=level)
        )

    def on_device_state_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        self._add(
            f"{payload['device_id']} turned {payload['status'].lower()}",
            NotificationLevel.SUCCESS if payload["status"] == "ON" else NotificationLevel.INFO,
        )

    def on_connectivity_changed(self, event: DomainEvent) -> None:
        payload = event.payload
        online = bool(payload["online"])
        self._add(
            f"{payload['device_id']} is {'online' if online else 'offline'}",
            NotificationLevel.INFO if online else NotificationLevel.WARNING,
        )

    def on_schedule_fired(self, event: DomainEvent) -> None:
        self._add("A scheduled action was applied", NotificationLevel.INFO)

    def on_automation_triggered(self, event: DomainEvent) -> None:
        self._add(
            f"Automation '{event.payload['name']}' ran", NotificationLevel.SUCCESS
        )

    def on_failure(self, event: DomainEvent) -> None:
        self._add(event.payload["reason"], NotificationLevel.ERROR)

    def list_notifications(self) -> tuple[Notification, ...]:
        return tuple(reversed(self._notifications.get_all()))

    @property
    def unread_count(self) -> int:
        return sum(1 for item in self._notifications.get_all() if not item.read)

    def mark_read(self, notification_id: str) -> Notification:
        notification = self._notifications.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError.for_id(notification_id)
        notification.mark_read()
        self._notifications.update(notification)
        return notification

    def delete(self, notification_id: str) -> Notification:
        notification = self._notifications.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError.for_id(notification_id)
        self._notifications.remove(notification_id)
        return notification

    def clear(self) -> None:
        self._notifications.clear()
