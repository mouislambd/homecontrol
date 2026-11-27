"""Domain-specific exception hierarchy.

All application errors inherit from ``SmartHomeError`` so the API layer can
translate them in one centralized handler. ``status_code`` and ``code`` are
class-level policy, not something each endpoint has to repeat.
"""


class SmartHomeError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class DeviceNotFoundError(SmartHomeError):
    status_code = 404
    code = "device_not_found"

    @classmethod
    def for_id(cls, device_id: str) -> "DeviceNotFoundError":
        return cls(f"Device '{device_id}' not found")


class RoomNotFoundError(SmartHomeError):
    status_code = 404
    code = "room_not_found"

    @classmethod
    def for_id(cls, room_id: str) -> "RoomNotFoundError":
        return cls(f"Room '{room_id}' not found")


class ScheduleNotFoundError(SmartHomeError):
    status_code = 404
    code = "schedule_not_found"

    @classmethod
    def for_id(cls, schedule_id: str) -> "ScheduleNotFoundError":
        return cls(f"Schedule '{schedule_id}' not found")


class RuleNotFoundError(SmartHomeError):
    status_code = 404
    code = "rule_not_found"

    @classmethod
    def for_id(cls, rule_id: str) -> "RuleNotFoundError":
        return cls(f"Automation rule '{rule_id}' not found")


class NotificationNotFoundError(SmartHomeError):
    status_code = 404
    code = "notification_not_found"

    @classmethod
    def for_id(cls, notification_id: str) -> "NotificationNotFoundError":
        return cls(f"Notification '{notification_id}' not found")


class ConflictError(SmartHomeError):
    status_code = 409
    code = "conflict"


class DeviceOfflineError(SmartHomeError):
    status_code = 409
    code = "device_offline"

    @classmethod
    def for_id(cls, device_id: str) -> "DeviceOfflineError":
        return cls(f"Device '{device_id}' is offline")
