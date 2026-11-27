"""Initial relational schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-26

Creates users, rooms, devices, schedules, automations, history, energy logs,
notifications and the room-membership/schedule-day child tables. No data is
inserted by this migration.
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

TIMESTAMP = dict(type_=sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", **TIMESTAMP),
        sa.Column("updated_at", **TIMESTAMP),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.CheckConstraint("length(trim(email)) > 0", name="ck_users_email_not_blank"),
        sa.CheckConstraint("length(trim(display_name)) > 0", name="ck_users_name_not_blank"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(200), server_default="", nullable=False),
        sa.Column("created_at", **TIMESTAMP),
        sa.Column("updated_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_rooms_name_not_blank"),
    )
    op.create_index("uq_rooms_owner_name", "rooms", ["owner_user_id", "name"], unique=True)

    op.create_table(
        "room_members",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.String(64), nullable=False),
        sa.Column("granted_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "room_id"),
    )
    op.create_index("ix_room_members_room", "room_members", ["room_id"])

    op.create_table(
        "devices",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.String(64), nullable=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("device_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(3), server_default="OFF", nullable=False),
        sa.Column("online", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("wattage", sa.Numeric(10, 3), server_default="0", nullable=False),
        sa.Column("last_state_change_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", **TIMESTAMP),
        sa.Column("updated_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("device_type IN ('light', 'fan', 'ac')", name="ck_devices_type"),
        sa.CheckConstraint("status IN ('ON', 'OFF')", name="ck_devices_status"),
        sa.CheckConstraint("wattage >= 0", name="ck_devices_wattage_positive"),
    )
    op.create_index("ix_devices_owner", "devices", ["owner_user_id"])
    op.create_index("ix_devices_room", "devices", ["room_id"])

    op.create_table(
        "device_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("previous_status", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("occurred_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "source IN ('api', 'schedule', 'automation', 'system')",
            name="ck_history_source",
        ),
    )
    op.create_index("ix_history_device_time", "device_history", ["device_id", "occurred_at"])
    op.create_index("ix_history_time", "device_history", ["occurred_at"])

    op.create_table(
        "energy_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("wattage", sa.Numeric(10, 3), nullable=False),
        sa.Column("estimated_energy_wh", sa.Numeric(14, 4), nullable=False),
        sa.Column("measurement_source", sa.String(16), server_default="estimated", nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("ended_at > started_at", name="ck_energy_interval"),
        sa.CheckConstraint("duration_seconds > 0", name="ck_energy_duration_positive"),
        sa.CheckConstraint("wattage >= 0", name="ck_energy_wattage_positive"),
        sa.CheckConstraint("estimated_energy_wh >= 0", name="ck_energy_wh_non_negative"),
        sa.CheckConstraint("measurement_source = 'estimated'", name="ck_energy_source_estimated"),
    )
    op.create_index("ix_energy_device_started", "energy_logs", ["device_id", "started_at"])

    op.create_table(
        "schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(3), nullable=False),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", **TIMESTAMP),
        sa.Column("updated_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("action IN ('ON', 'OFF')", name="ck_schedules_action"),
    )
    op.create_index("ix_schedules_enabled_time", "schedules", ["enabled", "time"])

    op.create_table(
        "schedule_days",
        sa.Column("schedule_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("schedule_id", "day"),
        sa.CheckConstraint("day BETWEEN 0 AND 6", name="ck_schedule_days_range"),
    )

    op.create_table(
        "automations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("trigger_device_id", sa.String(64), nullable=False),
        sa.Column("trigger_status", sa.String(3), nullable=False),
        sa.Column("target_device_id", sa.String(64), nullable=False),
        sa.Column("target_action", sa.String(3), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", **TIMESTAMP),
        sa.Column("updated_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trigger_device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("trigger_status IN ('ON', 'OFF')", name="ck_automations_trigger_status"),
        sa.CheckConstraint("target_action IN ('ON', 'OFF')", name="ck_automations_target_action"),
    )
    op.create_index("uq_automations_owner_name", "automations", ["owner_user_id", "name"], unique=True)
    op.create_index("ix_automations_lookup", "automations", ["enabled", "trigger_device_id", "trigger_status"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("level", sa.String(10), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", **TIMESTAMP),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "level IN ('info', 'success', 'warning', 'error')",
            name="ck_notifications_level",
        ),
    )
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])


def downgrade() -> None:
    for table in (
        "notifications",
        "automations",
        "schedule_days",
        "schedules",
        "energy_logs",
        "device_history",
        "devices",
        "room_members",
        "rooms",
        "users",
    ):
        op.drop_table(table)
