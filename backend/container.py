"""Composition root: the only module that knows concrete implementations.

FastAPI routes depend on provider functions here, so the HTTP layer never
imports a repository, an event broker or a concrete service constructor.
Storage is chosen once here: in-memory by default, SQLite when
``SMART_HOME_DB_PATH`` is configured.
"""

import logging
import os

logger = logging.getLogger(__name__)

try:
    from . import devices
    from .database import is_database_configured, session_scope
    from .db_repositories import (
        SqlActivityRepository,
        SqlDeviceRepository,
        SqlEnergyLogRepository,
        SqlNotificationRepository,
        SqlRoomRepository,
        SqlRuleRepository,
        SqlScheduleRepository,
    )
    from .domain import Room
    from .events import EventBroker
    from .persistence import (
        SQLiteRepository,
        decode_activity,
        decode_device,
        decode_notification,
        decode_rule,
        decode_room,
        decode_schedule,
        encode_activity,
        encode_device,
        encode_notification,
        encode_rule,
        encode_room,
        encode_schedule,
    )
    from .realtime import RealtimeHub
    from .repositories import InMemoryRepository
    from .services import (
        ActivityService,
        AutomationService,
        DeviceService,
        EnergyService,
        NotificationService,
        RoomService,
        ScheduleService,
    )
except ImportError:
    import devices
    from database import is_database_configured, session_scope
    from db_repositories import (
        SqlActivityRepository,
        SqlDeviceRepository,
        SqlEnergyLogRepository,
        SqlNotificationRepository,
        SqlRoomRepository,
        SqlRuleRepository,
        SqlScheduleRepository,
    )
    from domain import Room
    from events import EventBroker
    from persistence import (
        SQLiteRepository,
        decode_activity,
        decode_device,
        decode_notification,
        decode_rule,
        decode_room,
        decode_schedule,
        encode_activity,
        encode_device,
        encode_notification,
        encode_rule,
        encode_room,
        encode_schedule,
    )
    from realtime import RealtimeHub
    from repositories import InMemoryRepository
    from services import (
        ActivityService,
        AutomationService,
        DeviceService,
        EnergyService,
        NotificationService,
        RoomService,
        ScheduleService,
    )


EVENT_TOPICS = (
    "device.state_changed",
    "device.connectivity_changed",
    "device.temperature_changed",
    "device.created",
    "device.updated",
    "device.deleted",
    "device.room_changed",
    "room.created",
    "room.deleted",
    "schedule.fired",
    "schedule.failed",
    "automation.triggered",
    "automation.failed",
)


class AppContainer:
    """Wires repositories, services, events and real-time fan-out together."""

    def __init__(self, db_path: str | None = None, postgres: bool | None = None) -> None:
        self.db_path = db_path if db_path is not None else os.getenv(
            "SMART_HOME_DB_PATH", ""
        ).strip()
        self.postgres = postgres if postgres is not None else is_database_configured()
        if self.postgres:
            self.storage_mode = "postgresql"
        elif self.db_path:
            self.storage_mode = "sqlite_json"
        else:
            self.storage_mode = "memory"
        logger.info("storage backend selected: %s", self.storage_mode)
        self.events = EventBroker()
        self.realtime = RealtimeHub()
        self._build()
        if self.postgres and os.getenv("SEED_DEMO_DATA", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            try:
                from .seed import seed_demo_data
            except ImportError:
                from seed import seed_demo_data

            seed_demo_data()

    def _make_repository(self, table, key, encode, decode, items=()):
        if self.db_path:
            return SQLiteRepository(self.db_path, table, key, encode, decode)
        return InMemoryRepository(key, items=items)

    def _build(self, fresh: bool = False) -> None:
        if self.postgres:
            self.device_repository = SqlDeviceRepository()
            self.room_repository = SqlRoomRepository()
            self.schedule_repository = SqlScheduleRepository()
            self.rule_repository = SqlRuleRepository()
            self.activity_repository = SqlActivityRepository()
            self.notification_repository = SqlNotificationRepository()
            self.energy_log_repository = SqlEnergyLogRepository()
        else:
            self.device_repository = self._make_repository(
                "devices",
                lambda device: device.device_id,
                encode_device,
                decode_device,
                tuple(devices.get_devices().values()),
            )
            self.room_repository = self._make_repository(
                "rooms", lambda room: room.id, encode_room, decode_room
            )
            self.schedule_repository = self._make_repository(
                "schedules", lambda item: item.id, encode_schedule, decode_schedule
            )
            self.rule_repository = self._make_repository(
                "rules", lambda item: item.id, encode_rule, decode_rule
            )
            self.activity_repository = self._make_repository(
                "activity", lambda item: item.id, encode_activity, decode_activity
            )
            self.notification_repository = self._make_repository(
                "notifications", lambda item: item.id, encode_notification, decode_notification
            )
            self.energy_log_repository = None

        if fresh and not self.postgres:
            for repository in (
                self.device_repository,
                self.room_repository,
                self.schedule_repository,
                self.rule_repository,
                self.activity_repository,
                self.notification_repository,
            ):
                repository.clear()

        if not self.postgres and len(self.device_repository) == 0:
            for device in devices.get_devices().values():
                self.device_repository.add(device)

        self.device_service = DeviceService(
            self.device_repository,
            self.events,
            energy_logs=self.energy_log_repository,
            transaction=session_scope if self.postgres else None,
        )
        self.energy_service = EnergyService(
            self.device_repository, self.energy_log_repository
        )
        self.room_service = RoomService(
            self.room_repository, self.device_repository, self.events
        )
        self.schedule_service = ScheduleService(
            self.schedule_repository, self.device_service, self.events
        )
        self.automation_service = AutomationService(
            self.rule_repository, self.device_service, self.events
        )
        self.activity_service = ActivityService(self.activity_repository)
        self.notification_service = NotificationService(self.notification_repository)

        if not self.postgres and len(self.room_repository) == 0:
            self._seed_rooms()
        self._subscribe()

    def _seed_rooms(self) -> None:
        for room in (
            Room(id="living-room", name="Living Room", description="Main living area"),
            Room(id="bedroom", name="Bedroom", description="Private sleeping area"),
        ):
            self.room_repository.add(room)
        for device_id, room_id in (
            ("light", "living-room"),
            ("ac", "living-room"),
            ("fan", "bedroom"),
        ):
            device = self.device_repository.get(device_id)
            if device is not None:
                device.assign_room(room_id)
                self.device_repository.update(device)

    def _subscribe(self) -> None:
        self.events.clear_subscribers()
        self.events.subscribe(
            "device.state_changed", self.activity_service.on_device_state_changed
        )
        self.events.subscribe(
            "device.connectivity_changed",
            self.activity_service.on_connectivity_changed,
        )
        self.events.subscribe(
            "device.state_changed", self.notification_service.on_device_state_changed
        )
        self.events.subscribe(
            "device.connectivity_changed",
            self.notification_service.on_connectivity_changed,
        )
        self.events.subscribe(
            "device.state_changed", self.automation_service.on_device_state_changed
        )
        self.events.subscribe(
            "device.temperature_changed", self.automation_service.on_temperature_changed
        )
        self.events.subscribe(
            "device.temperature_changed", self.activity_service.on_temperature_changed
        )
        self.events.subscribe(
            "schedule.fired", self.notification_service.on_schedule_fired
        )
        self.events.subscribe(
            "automation.triggered", self.notification_service.on_automation_triggered
        )
        for topic in ("schedule.failed", "automation.failed"):
            self.events.subscribe(topic, self.notification_service.on_failure)
        for topic in EVENT_TOPICS:
            self.events.subscribe(topic, self.realtime.publish)

    def reset(self) -> None:
        devices.reset_devices()
        self.events.clear()
        self._build(fresh=True)


_container = AppContainer()


def get_container() -> AppContainer:
    return _container


def get_storage_mode() -> str:
    return _container.storage_mode


def get_realtime_hub() -> RealtimeHub:
    return _container.realtime


def get_device_service():
    return _container.device_service


def get_energy_service():
    return _container.energy_service


def get_room_service():
    return _container.room_service


def get_schedule_service():
    return _container.schedule_service


def get_automation_service():
    return _container.automation_service


def get_activity_service():
    return _container.activity_service


def get_notification_service():
    return _container.notification_service


def get_event_publisher():
    return _container.events


def reset_state() -> None:
    _container.reset()
