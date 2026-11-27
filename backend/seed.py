"""Explicit, opt-in demo data seeding.

Never called automatically on application startup. It inserts the same default
devices and rooms the in-memory container used, so API contracts stay identical.
"""

try:
    from .db_repositories import DEMO_USER_ID
    from .devices import create_devices
    from .models import DeviceModel, RoomModel, UserModel
    from .database import session_scope
except ImportError:
    from db_repositories import DEMO_USER_ID
    from devices import create_devices
    from models import DeviceModel, RoomModel, UserModel
    from database import session_scope


ROOM_ASSIGNMENTS = {
    "light": "living-room",
    "ac": "living-room",
    "fan": "bedroom",
}


def seed_demo_data() -> None:
    """Insert the demo user, rooms and devices once; leave existing data alone."""
    from datetime import datetime, timezone

    with session_scope() as session:
        if session.get(UserModel, DEMO_USER_ID) is not None:
            return

        session.add(
            UserModel(
                id=DEMO_USER_ID,
                email="demo@smart-home.local",
                display_name="Demo User",
            )
        )
        session.add_all(
            [
                RoomModel(
                    id="living-room",
                    owner_user_id=DEMO_USER_ID,
                    name="Living Room",
                    description="Main living area",
                ),
                RoomModel(
                    id="bedroom",
                    owner_user_id=DEMO_USER_ID,
                    name="Bedroom",
                    description="Private sleeping area",
                ),
            ]
        )
        for device in create_devices().values():
            session.add(
                DeviceModel(
                    id=device.device_id,
                    owner_user_id=DEMO_USER_ID,
                    room_id=ROOM_ASSIGNMENTS.get(device.device_id),
                    name=device.name,
                    device_type=device.device_type.value,
                    status=device.status,
                    online=True,
                    wattage=device.energy_meter.wattage,
                    last_state_change_at=datetime.now(timezone.utc),
                )
            )
