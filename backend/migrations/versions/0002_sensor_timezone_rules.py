"""Add simulated temperature input, schedule timezone and threshold automation.

Revision ID: 0002_sensor_timezone_rules
Revises: 0001_initial_schema
Create Date: 2026-11-26

Additive only: no columns are dropped and no existing rows are modified beyond
population of the new default values.
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_sensor_timezone_rules"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("devices") as batch:
        batch.add_column(sa.Column("temperature_c", sa.Numeric(6, 2), nullable=True))
        batch.add_column(sa.Column("temperature_source", sa.String(16), nullable=True))
        batch.create_check_constraint(
            "ck_devices_temperature_source",
            "temperature_source IS NULL OR temperature_source = 'simulated'",
        )

    with op.batch_alter_table("schedules") as batch:
        batch.add_column(
            sa.Column(
                "timezone", sa.String(64), server_default="UTC", nullable=False
            )
        )

    with op.batch_alter_table("automations") as batch:
        batch.add_column(
            sa.Column(
                "trigger_type",
                sa.String(24),
                server_default="device_state",
                nullable=False,
            )
        )
        batch.add_column(sa.Column("threshold_c", sa.Numeric(6, 2), nullable=True))
        batch.create_check_constraint(
            "ck_automations_trigger_type",
            "trigger_type IN ('device_state', 'temperature_above', 'temperature_below')",
        )


def downgrade() -> None:
    with op.batch_alter_table("automations") as batch:
        batch.drop_constraint("ck_automations_trigger_type", type_="check")
        batch.drop_column("threshold_c")
        batch.drop_column("trigger_type")
    with op.batch_alter_table("schedules") as batch:
        batch.drop_column("timezone")
    with op.batch_alter_table("devices") as batch:
        batch.drop_constraint("ck_devices_temperature_source", type_="check")
        batch.drop_column("temperature_source")
        batch.drop_column("temperature_c")
