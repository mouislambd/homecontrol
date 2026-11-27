"""Optional SQLite persistence behind the same ``Repository`` contract.

Selected with ``SMART_HOME_DB_PATH``. The default remains in-memory, which
keeps tests deterministic and Render's ephemeral filesystem unnecessary. No
third-party dependency is introduced: everything uses the standard library.
"""

import json
import sqlite3
from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime
from threading import RLock
from typing import Generic, TypeVar

try:
    from .domain import (
        ActivityEvent,
        AutomationRule,
        BaseDevice,
        DeviceStatus,
        DeviceType,
        EventSource,
        Notification,
        NotificationLevel,
        PowerAction,
        Room,
        Schedule,
        TriggerType,
    )
    from .exceptions import ConflictError
    from .interfaces import Repository
except ImportError:
    from domain import (
        ActivityEvent,
        AutomationRule,
        BaseDevice,
        DeviceStatus,
        DeviceType,
        EventSource,
        Notification,
        NotificationLevel,
        PowerAction,
        Room,
        Schedule,
        TriggerType,
    )
    from exceptions import ConflictError
    from interfaces import Repository

T = TypeVar("T")


class SQLiteRepository(Repository[T], Generic[T]):
    def __init__(
        self,
        path: str,
        table: str,
        key: Callable[[T], str],
        encode: Callable[[T], dict],
        decode: Callable[[dict], T],
    ) -> None:
        self._key = key
        self._encode = encode
        self._decode = decode
        self._lock = RLock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.execute(
            f"CREATE TABLE IF NOT EXISTS {table} "
            "(id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        self._connection.commit()
        self._table = table

    def add(self, item: T) -> T:
        with self._lock, self._connection:
            item_id = self._key(item)
            try:
                self._connection.execute(
                    f"INSERT INTO {self._table} (id, data) VALUES (?, ?)",
                    (item_id, json.dumps(self._encode(item))),
                )
            except sqlite3.IntegrityError as exc:
                raise ConflictError(f"Item '{item_id}' already exists") from exc
        return item

    def get(self, item_id: str) -> T | None:
        with self._lock:
            row = self._connection.execute(
                f"SELECT data FROM {self._table} WHERE id = ?", (item_id,)
            ).fetchone()
        return self._decode(json.loads(row[0])) if row else None

    def get_all(self) -> tuple[T, ...]:
        with self._lock:
            rows = self._connection.execute(
                f"SELECT data FROM {self._table}"
            ).fetchall()
        return tuple(self._decode(json.loads(row[0])) for row in rows)

    def update(self, item: T) -> T:
        with self._lock, self._connection:
            cursor = self._connection.execute(
                f"UPDATE {self._table} SET data = ? WHERE id = ?",
                (json.dumps(self._encode(item)), self._key(item)),
            )
            if cursor.rowcount == 0:
                raise ConflictError(f"Item '{self._key(item)}' does not exist")
        return item

    def remove(self, item_id: str) -> T | None:
        item = self.get(item_id)
        if item is None:
            return None
        with self._lock, self._connection:
            self._connection.execute(
                f"DELETE FROM {self._table} WHERE id = ?", (item_id,)
            )
        return item

    def clear(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(f"DELETE FROM {self._table}")

    def __len__(self) -> int:
        with self._lock:
            return self._connection.execute(
                f"SELECT COUNT(*) FROM {self._table}"
            ).fetchone()[0]


def encode_device(device) -> dict:
    return {
        "id": device.device_id,
        "name": device.name,
        "device_type": device.device_type.value,
        "status": device.status,
        "wattage": device.energy_meter.wattage,
        "energy_wh": device.energy_meter.reading(),
        "room_id": device.room_id,
        "online": device.online,
        "temperature_c": device.temperature_c,
    }


def decode_device(raw: dict) -> BaseDevice:
    device = BaseDevice(
        raw["id"],
        raw["name"],
        DeviceType(raw["device_type"]),
        raw["status"],
        raw["wattage"],
        raw.get("room_id"),
        raw.get("online", True),
        raw.get("temperature_c"),
    )
    device.energy_meter.total_wh = raw.get("energy_wh", 0.0)
    return device


def encode_room(room: Room) -> dict:
    return asdict(room)


def decode_room(raw: dict) -> Room:
    return Room(**raw)


def encode_schedule(schedule: Schedule) -> dict:
    data = asdict(schedule)
    data["days"] = list(schedule.days)
    data["last_run"] = schedule.last_run.isoformat() if schedule.last_run else None
    data["timezone"] = schedule.timezone
    return data


def decode_schedule(raw: dict) -> Schedule:
    return Schedule(
        id=raw["id"],
        device_id=raw["device_id"],
        action=PowerAction(raw["action"]),
        time=raw["time"],
        days=tuple(raw["days"]),
        enabled=raw["enabled"],
        last_run=datetime.fromisoformat(raw["last_run"]) if raw["last_run"] else None,
        timezone=raw.get("timezone", "UTC"),
    )


def encode_rule(rule: AutomationRule) -> dict:
    data = asdict(rule)
    data["trigger_status"] = rule.trigger_status.value
    data["target_action"] = rule.target_action.value
    data["trigger_type"] = rule.trigger_type.value
    data["threshold_c"] = rule.threshold_c
    return data


def decode_rule(raw: dict) -> AutomationRule:
    return AutomationRule(
        id=raw["id"],
        name=raw["name"],
        trigger_device_id=raw["trigger_device_id"],
        trigger_status=DeviceStatus(raw["trigger_status"]),
        target_device_id=raw["target_device_id"],
        target_action=PowerAction(raw["target_action"]),
        enabled=raw["enabled"],
        trigger_type=TriggerType(raw.get("trigger_type", "device_state")),
        threshold_c=raw.get("threshold_c"),
    )


def encode_activity(event: ActivityEvent) -> dict:
    data = asdict(event)
    data["source"] = event.source.value
    data["occurred_at"] = event.occurred_at.isoformat()
    return data


def decode_activity(raw: dict) -> ActivityEvent:
    return ActivityEvent(
        id=raw["id"],
        device_id=raw["device_id"],
        action=raw["action"],
        previous_status=raw["previous_status"],
        status=raw["status"],
        source=EventSource(raw["source"]),
        occurred_at=datetime.fromisoformat(raw["occurred_at"]),
    )


def encode_notification(item: Notification) -> dict:
    data = asdict(item)
    data["level"] = item.level.value
    data["created_at"] = item.created_at.isoformat()
    return data


def decode_notification(raw: dict) -> Notification:
    return Notification(
        id=raw["id"],
        message=raw["message"],
        level=NotificationLevel(raw["level"]),
        read=raw["read"],
        created_at=datetime.fromisoformat(raw["created_at"]),
    )
