"""SQLAlchemy repository implementations behind the existing Repository contract.

ORM objects never leave this layer: each repository translates rows to the
domain dataclasses used by services, preserving OOP behaviour and API shapes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

try:
    from .database import session_scope
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
        utcnow,
    )
    from .exceptions import ConflictError
    from .interfaces import Repository, SmartDevice
    from .models import (
        AutomationModel,
        DeviceHistoryModel,
        DeviceModel,
        EnergyLogModel,
        NotificationModel,
        RoomModel,
        ScheduleDayModel,
        ScheduleModel,
    )
except ImportError:
    from database import session_scope
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
        utcnow,
    )
    from exceptions import ConflictError
    from interfaces import Repository, SmartDevice
    from models import (
        AutomationModel,
        DeviceHistoryModel,
        DeviceModel,
        EnergyLogModel,
        NotificationModel,
        RoomModel,
        ScheduleDayModel,
        ScheduleModel,
    )

T = TypeVar("T")
DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _as_uuid(value: str) -> UUID:
    return UUID(value.replace("-", "").zfill(32)[:32])


def _as_float(value: object) -> float:
    return float(value) if isinstance(value, Decimal) else float(value or 0)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class SqlDeviceRepository(Repository[SmartDevice]):
    def _to_domain(self, row: DeviceModel, session) -> SmartDevice:
        device = BaseDevice(
            row.id,
            row.name,
            DeviceType(row.device_type),
            row.status,
            wattage=_as_float(row.wattage),
            room_id=row.room_id,
            online=bool(row.online),
            temperature_c=_as_float(row.temperature_c) if row.temperature_c is not None else None,
        )
        total = session.scalar(
            select(func.coalesce(func.sum(EnergyLogModel.estimated_energy_wh), 0)).where(
                EnergyLogModel.device_id == row.id
            )
        )
        device.temperature_source = row.temperature_source
        device.energy_meter.total_wh = _as_float(total)
        device.energy_meter._since = (
            _aware(row.last_state_change_at) if row.status == "ON" else None
        )
        return device

    def add(self, item: SmartDevice) -> SmartDevice:
        with session_scope() as session:
            row = DeviceModel(
                id=item.device_id,
                owner_user_id=DEMO_USER_ID,
                room_id=item.room_id,
                name=item.name,
                device_type=item.device_type.value,
                status=item.status,
                online=item.online,
                wattage=item.energy_meter.wattage,
                temperature_c=item.temperature_c,
                temperature_source=item.temperature_source,
                last_state_change_at=utcnow(),
            )
            session.add(row)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ConflictError(f"Device '{item.device_id}' already exists") from exc
        return item

    def get(self, item_id: str) -> SmartDevice | None:
        with session_scope() as session:
            row = session.get(DeviceModel, item_id)
            return self._to_domain(row, session) if row else None

    def get_all(self) -> tuple[SmartDevice, ...]:
        with session_scope() as session:
            rows = session.scalars(select(DeviceModel).order_by(DeviceModel.id)).all()
            return tuple(self._to_domain(row, session) for row in rows)

    def update(self, item: SmartDevice) -> SmartDevice:
        with session_scope() as session:
            row = session.get(DeviceModel, item.device_id)
            if row is None:
                raise ConflictError(f"Device '{item.device_id}' does not exist")
            status_changed = row.status != item.status
            row.name = item.name
            row.room_id = item.room_id
            row.device_type = item.device_type.value
            row.status = item.status
            row.online = item.online
            row.wattage = item.energy_meter.wattage
            row.temperature_c = item.temperature_c
            row.temperature_source = item.temperature_source
            if status_changed:
                row.last_state_change_at = utcnow()
        return item

    def remove(self, item_id: str) -> SmartDevice | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(DeviceModel, item_id)
            if row is not None:
                session.delete(row)
        return item


class SqlRoomRepository(Repository[Room]):
    def add(self, item: Room) -> Room:
        with session_scope() as session:
            session.add(
                RoomModel(
                    id=item.id,
                    owner_user_id=DEMO_USER_ID,
                    name=item.name,
                    description=item.description,
                )
            )
            try:
                session.flush()
            except IntegrityError as exc:
                raise ConflictError(f"Room '{item.name}' already exists") from exc
        return item

    def get(self, item_id: str) -> Room | None:
        with session_scope() as session:
            row = session.get(RoomModel, item_id)
            return Room(row.id, row.name, row.description) if row else None

    def get_all(self) -> tuple[Room, ...]:
        with session_scope() as session:
            rows = session.scalars(select(RoomModel).order_by(RoomModel.name)).all()
            return tuple(Room(row.id, row.name, row.description) for row in rows)

    def update(self, item: Room) -> Room:
        with session_scope() as session:
            row = session.get(RoomModel, item.id)
            if row is None:
                raise ConflictError(f"Room '{item.id}' does not exist")
            row.name = item.name
            row.description = item.description
            try:
                session.flush()
            except IntegrityError as exc:
                raise ConflictError(f"Room '{item.name}' already exists") from exc
        return item

    def remove(self, item_id: str) -> Room | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(RoomModel, item_id)
            if row is not None:
                session.delete(row)
        return item


class SqlScheduleRepository(Repository[Schedule]):
    def _to_domain(self, row: ScheduleModel) -> Schedule:
        return Schedule(
            id=str(row.id),
            device_id=row.device_id,
            action=PowerAction(row.action),
            time=row.time.strftime("%H:%M"),
            days=tuple(sorted(item.day for item in row.days)),
            enabled=bool(row.enabled),
            last_run=_aware(row.last_run_at),
            timezone=row.timezone or "UTC",
        )

    def add(self, item: Schedule) -> Schedule:
        with session_scope() as session:
            row = ScheduleModel(
                id=_as_uuid(item.id),
                owner_user_id=DEMO_USER_ID,
                device_id=item.device_id,
                action=item.action.value,
                time=datetime.strptime(item.time, "%H:%M").time(),
                enabled=item.enabled,
                timezone=item.timezone,
                last_run_at=item.last_run,
            )
            session.add(row)
            session.flush()
            item.id = str(row.id)
            session.add_all(
                ScheduleDayModel(schedule_id=row.id, day=day) for day in item.days
            )
        return item

    def get(self, item_id: str) -> Schedule | None:
        with session_scope() as session:
            row = session.get(ScheduleModel, _as_uuid(item_id))
            return self._to_domain(row) if row else None

    def get_all(self) -> tuple[Schedule, ...]:
        with session_scope() as session:
            rows = session.scalars(select(ScheduleModel).order_by(ScheduleModel.time)).all()
            return tuple(self._to_domain(row) for row in rows)

    def update(self, item: Schedule) -> Schedule:
        with session_scope() as session:
            row = session.get(ScheduleModel, _as_uuid(item.id))
            if row is None:
                raise ConflictError(f"Schedule '{item.id}' does not exist")
            row.device_id = item.device_id
            row.action = item.action.value
            row.time = datetime.strptime(item.time, "%H:%M").time()
            row.enabled = item.enabled
            row.timezone = item.timezone
            row.last_run_at = item.last_run
            session.query(ScheduleDayModel).filter(
                ScheduleDayModel.schedule_id == row.id
            ).delete()
            session.add_all(
                ScheduleDayModel(schedule_id=row.id, day=day) for day in item.days
            )
        return item

    def remove(self, item_id: str) -> Schedule | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(ScheduleModel, _as_uuid(item_id))
            if row is not None:
                session.delete(row)
        return item


class SqlRuleRepository(Repository[AutomationRule]):
    def _to_domain(self, row: AutomationModel) -> AutomationRule:
        return AutomationRule(
            id=str(row.id),
            name=row.name,
            trigger_device_id=row.trigger_device_id,
            trigger_status=DeviceStatus(row.trigger_status),
            target_device_id=row.target_device_id,
            target_action=PowerAction(row.target_action),
            enabled=bool(row.enabled),
            trigger_type=TriggerType(row.trigger_type or "device_state"),
            threshold_c=_as_float(row.threshold_c) if row.threshold_c is not None else None,
        )

    def add(self, item: AutomationRule) -> AutomationRule:
        with session_scope() as session:
            row = AutomationModel(
                id=_as_uuid(item.id),
                owner_user_id=DEMO_USER_ID,
                name=item.name,
                trigger_device_id=item.trigger_device_id,
                trigger_status=item.trigger_status.value,
                target_device_id=item.target_device_id,
                target_action=item.target_action.value,
                enabled=item.enabled,
                trigger_type=item.trigger_type.value,
                threshold_c=item.threshold_c,
            )
            session.add(row)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ConflictError(f"Automation rule '{item.name}' already exists") from exc
            item.id = str(row.id)
        return item

    def get(self, item_id: str) -> AutomationRule | None:
        with session_scope() as session:
            row = session.get(AutomationModel, _as_uuid(item_id))
            return self._to_domain(row) if row else None

    def get_all(self) -> tuple[AutomationRule, ...]:
        with session_scope() as session:
            rows = session.scalars(select(AutomationModel).order_by(AutomationModel.name)).all()
            return tuple(self._to_domain(row) for row in rows)

    def update(self, item: AutomationRule) -> AutomationRule:
        with session_scope() as session:
            row = session.get(AutomationModel, _as_uuid(item.id))
            if row is None:
                raise ConflictError(f"Automation rule '{item.id}' does not exist")
            row.name = item.name
            row.trigger_device_id = item.trigger_device_id
            row.trigger_status = item.trigger_status.value
            row.target_device_id = item.target_device_id
            row.target_action = item.target_action.value
            row.enabled = item.enabled
            row.trigger_type = item.trigger_type.value
            row.threshold_c = item.threshold_c
        return item

    def remove(self, item_id: str) -> AutomationRule | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(AutomationModel, _as_uuid(item_id))
            if row is not None:
                session.delete(row)
        return item


class SqlActivityRepository(Repository[ActivityEvent]):
    def add(self, item: ActivityEvent) -> ActivityEvent:
        with session_scope() as session:
            row = DeviceHistoryModel(
                id=_as_uuid(item.id),
                device_id=item.device_id,
                user_id=DEMO_USER_ID,
                action=item.action,
                previous_status=item.previous_status,
                status=item.status,
                source=item.source.value,
                occurred_at=item.occurred_at,
            )
            session.add(row)
            session.flush()
            item.id = str(row.id)
        return item

    def get(self, item_id: str) -> ActivityEvent | None:
        with session_scope() as session:
            row = session.get(DeviceHistoryModel, _as_uuid(item_id))
            return self._to_domain(row) if row else None

    def _to_domain(self, row: DeviceHistoryModel) -> ActivityEvent:
        return ActivityEvent(
            id=str(row.id),
            device_id=row.device_id,
            action=row.action,
            previous_status=row.previous_status,
            status=row.status,
            source=EventSource(row.source),
            occurred_at=_aware(row.occurred_at) or utcnow(),
        )

    def get_all(self) -> tuple[ActivityEvent, ...]:
        with session_scope() as session:
            rows = session.scalars(
                select(DeviceHistoryModel).order_by(DeviceHistoryModel.occurred_at)
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    def update(self, item: ActivityEvent) -> ActivityEvent:
        return item

    def remove(self, item_id: str) -> ActivityEvent | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(DeviceHistoryModel, _as_uuid(item_id))
            if row is not None:
                session.delete(row)
        return item


class SqlNotificationRepository(Repository[Notification]):
    def _to_domain(self, row: NotificationModel) -> Notification:
        return Notification(
            id=str(row.id),
            message=row.message,
            level=NotificationLevel(row.level),
            read=bool(row.is_read),
            created_at=_aware(row.created_at) or utcnow(),
        )

    def add(self, item: Notification) -> Notification:
        with session_scope() as session:
            row = NotificationModel(
                id=_as_uuid(item.id),
                user_id=DEMO_USER_ID,
                message=item.message,
                level=item.level.value,
                is_read=item.read,
            )
            session.add(row)
            session.flush()
            item.id = str(row.id)
        return item

    def get(self, item_id: str) -> Notification | None:
        with session_scope() as session:
            row = session.get(NotificationModel, _as_uuid(item_id))
            return self._to_domain(row) if row else None

    def get_all(self) -> tuple[Notification, ...]:
        with session_scope() as session:
            rows = session.scalars(
                select(NotificationModel).order_by(NotificationModel.created_at)
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    def update(self, item: Notification) -> Notification:
        with session_scope() as session:
            row = session.get(NotificationModel, _as_uuid(item.id))
            if row is None:
                raise ConflictError(f"Notification '{item.id}' does not exist")
            row.is_read = item.read
        return item

    def remove(self, item_id: str) -> Notification | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(NotificationModel, _as_uuid(item_id))
            if row is not None:
                session.delete(row)
        return item

    def clear(self) -> None:
        with session_scope() as session:
            session.query(NotificationModel).delete()


class SqlEnergyLogRepository(Repository[EnergyLog]):
    def _to_domain(self, row: EnergyLogModel) -> EnergyLog:
        return EnergyLog(
            id=row.id,
            device_id=row.device_id,
            started_at=_aware(row.started_at) or utcnow(),
            ended_at=_aware(row.ended_at) or utcnow(),
            duration_seconds=float(row.duration_seconds),
            wattage=_as_float(row.wattage),
            estimated_energy_wh=_as_float(row.estimated_energy_wh),
            measurement_source=row.measurement_source,
        )

    def add(self, item: EnergyLog) -> EnergyLog:
        with session_scope() as session:
            row = EnergyLogModel(
                device_id=item.device_id,
                started_at=item.started_at,
                ended_at=item.ended_at,
                duration_seconds=item.duration_seconds,
                wattage=item.wattage,
                estimated_energy_wh=item.estimated_energy_wh,
                measurement_source=item.measurement_source,
            )
            session.add(row)
            session.flush()
            item.id = row.id
        return item

    def get(self, item_id: str) -> EnergyLog | None:
        with session_scope() as session:
            row = session.get(EnergyLogModel, int(item_id))
            return self._to_domain(row) if row else None

    def get_all(self) -> tuple[EnergyLog, ...]:
        with session_scope() as session:
            rows = session.scalars(
                select(EnergyLogModel).order_by(EnergyLogModel.started_at.desc())
            ).all()
            return tuple(self._to_domain(row) for row in rows)

    def logs_for(self, device_id: str | None, limit: int) -> tuple[EnergyLog, ...]:
        statement = select(EnergyLogModel).order_by(EnergyLogModel.started_at.desc()).limit(limit)
        if device_id:
            statement = statement.where(EnergyLogModel.device_id == device_id)
        with session_scope() as session:
            rows = session.scalars(statement).all()
            return tuple(self._to_domain(row) for row in rows)

    def update(self, item: EnergyLog) -> EnergyLog:
        return item

    def remove(self, item_id: str) -> EnergyLog | None:
        item = self.get(item_id)
        if item is None:
            return None
        with session_scope() as session:
            row = session.get(EnergyLogModel, int(item_id))
            if row is not None:
                session.delete(row)
        return item
