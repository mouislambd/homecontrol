"""SQLAlchemy 2.0 persistence models.

These are storage-layer representations only. Domain dataclasses in ``domain.py``
remain the objects services operate on; repositories translate between the two.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative registry shared by models and Alembic metadata."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rooms: Mapped[list["RoomModel"]] = relationship(back_populates="owner")
    room_memberships: Mapped[list["RoomMemberModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    devices: Mapped[list["DeviceModel"]] = relationship(back_populates="owner")
    schedules: Mapped[list["ScheduleModel"]] = relationship(back_populates="owner")
    automations: Mapped[list["AutomationModel"]] = relationship(back_populates="owner")
    history: Mapped[list["DeviceHistoryModel"]] = relationship(back_populates="user")
    notifications: Mapped[list["NotificationModel"]] = relationship(back_populates="user")

    __table_args__ = (
        CheckConstraint("length(trim(email)) > 0", name="ck_users_email_not_blank"),
        CheckConstraint("length(trim(display_name)) > 0", name="ck_users_name_not_blank"),
    )


class RoomModel(TimestampMixin, Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(200), default="", nullable=False)

    owner: Mapped["UserModel"] = relationship(back_populates="rooms")
    members: Mapped[list["RoomMemberModel"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    devices: Mapped[list["DeviceModel"]] = relationship(back_populates="room")

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_rooms_name_not_blank"),
        Index("uq_rooms_owner_name", "owner_user_id", "name", unique=True),
    )


class RoomMemberModel(Base):
    __tablename__ = "room_members"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    room_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["UserModel"] = relationship(back_populates="room_memberships")
    room: Mapped["RoomModel"] = relationship(back_populates="members")

    __table_args__ = (Index("ix_room_members_room", "room_id"),)


class DeviceModel(TimestampMixin, Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    device_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(3), default="OFF", nullable=False)
    online: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    wattage: Mapped[float] = mapped_column(Numeric(10, 3), default=0, nullable=False)
    temperature_c: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    temperature_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_state_change_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["UserModel"] = relationship(back_populates="devices")
    room: Mapped["RoomModel | None"] = relationship(back_populates="devices")
    history: Mapped[list["DeviceHistoryModel"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    energy_logs: Mapped[list["EnergyLogModel"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    schedules: Mapped[list["ScheduleModel"]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )
    triggered_rules: Mapped[list["AutomationModel"]] = relationship(
        back_populates="trigger_device",
        foreign_keys="AutomationModel.trigger_device_id",
        cascade="all, delete-orphan",
    )
    target_rules: Mapped[list["AutomationModel"]] = relationship(
        back_populates="target_device",
        foreign_keys="AutomationModel.target_device_id",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "device_type IN ('light', 'fan', 'ac')", name="ck_devices_type"
        ),
        CheckConstraint("status IN ('ON', 'OFF')", name="ck_devices_status"),
        CheckConstraint("wattage >= 0", name="ck_devices_wattage_positive"),
        CheckConstraint(
            "temperature_source IS NULL OR temperature_source = 'simulated'",
            name="ck_devices_temperature_source",
        ),
        Index("ix_devices_owner", "owner_user_id"),
        Index("ix_devices_room", "room_id"),
    )


class DeviceHistoryModel(Base):
    __tablename__ = "device_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    device: Mapped["DeviceModel"] = relationship(back_populates="history")
    user: Mapped["UserModel | None"] = relationship(back_populates="history")

    __table_args__ = (
        CheckConstraint(
            "source IN ('api', 'schedule', 'automation', 'system')",
            name="ck_history_source",
        ),
        Index("ix_history_device_time", "device_id", occurred_at.desc()),
        Index("ix_history_time", occurred_at.desc()),
    )


class EnergyLogModel(Base):
    __tablename__ = "energy_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    wattage: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    estimated_energy_wh: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    measurement_source: Mapped[str] = mapped_column(
        String(16), default="estimated", nullable=False
    )

    device: Mapped["DeviceModel"] = relationship(back_populates="energy_logs")

    __table_args__ = (
        CheckConstraint("ended_at > started_at", name="ck_energy_interval"),
        CheckConstraint("duration_seconds > 0", name="ck_energy_duration_positive"),
        CheckConstraint("wattage >= 0", name="ck_energy_wattage_positive"),
        CheckConstraint(
            "estimated_energy_wh >= 0", name="ck_energy_wh_non_negative"
        ),
        CheckConstraint(
            "measurement_source = 'estimated'", name="ck_energy_source_estimated"
        ),
        Index("ix_energy_device_started", "device_id", started_at.desc()),
    )


class ScheduleModel(TimestampMixin, Base):
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(3), nullable=False)
    time: Mapped[datetime] = mapped_column(Time, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped["UserModel"] = relationship(back_populates="schedules")
    device: Mapped["DeviceModel"] = relationship(back_populates="schedules")
    days: Mapped[list["ScheduleDayModel"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("action IN ('ON', 'OFF')", name="ck_schedules_action"),
        Index("ix_schedules_enabled_time", "enabled", "time"),
    )


class ScheduleDayModel(Base):
    __tablename__ = "schedule_days"

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schedules.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[int] = mapped_column(SmallInteger, primary_key=True)

    schedule: Mapped["ScheduleModel"] = relationship(back_populates="days")

    __table_args__ = (
        CheckConstraint("day BETWEEN 0 AND 6", name="ck_schedule_days_range"),
    )


class AutomationModel(TimestampMixin, Base):
    __tablename__ = "automations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    trigger_device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    trigger_status: Mapped[str] = mapped_column(String(3), nullable=False)
    target_device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    target_action: Mapped[str] = mapped_column(String(3), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        String(24), default="device_state", nullable=False
    )
    threshold_c: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    owner: Mapped["UserModel"] = relationship(back_populates="automations")
    trigger_device: Mapped["DeviceModel"] = relationship(
        back_populates="triggered_rules", foreign_keys=[trigger_device_id]
    )
    target_device: Mapped["DeviceModel"] = relationship(
        back_populates="target_rules", foreign_keys=[target_device_id]
    )

    __table_args__ = (
        CheckConstraint(
            "trigger_status IN ('ON', 'OFF')", name="ck_automations_trigger_status"
        ),
        CheckConstraint(
            "target_action IN ('ON', 'OFF')", name="ck_automations_target_action"
        ),
        CheckConstraint(
            "trigger_type IN ('device_state', 'temperature_above', 'temperature_below')",
            name="ck_automations_trigger_type",
        ),
        Index("uq_automations_owner_name", "owner_user_id", "name", unique=True),
        Index(
            "ix_automations_lookup", "enabled", "trigger_device_id", "trigger_status"
        ),
    )


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["UserModel"] = relationship(back_populates="notifications")

    __table_args__ = (
        CheckConstraint(
            "level IN ('info', 'success', 'warning', 'error')",
            name="ck_notifications_level",
        ),
        Index("ix_notifications_user_created", "user_id", created_at.desc()),
    )
