from fastapi.testclient import TestClient

from backend.container import AppContainer, get_container
from backend.domain import Room
from backend.main import app
from backend.persistence import SQLiteRepository, decode_room, encode_room


def test_websocket_broadcasts_domain_events():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as websocket:
            assert websocket.receive_json()["event"] == "connected"

            response = client.post("/devices/light/off")

            assert response.status_code == 200
            message = websocket.receive_json()
            assert message["event"] == "device.state_changed"
            assert message["payload"]["device_id"] == "light"
            assert message["payload"]["status"] == "OFF"


def test_sqlite_repository_round_trip(tmp_path):
    repository = SQLiteRepository(
        str(tmp_path / "rooms.db"),
        "rooms",
        lambda room: room.id,
        encode_room,
        decode_room,
    )
    repository.add(Room("r1", "Room One", "First"))

    assert repository.get("r1").name == "Room One"
    assert [room.id for room in repository.get_all()] == ["r1"]

    repository.update(Room("r1", "Renamed", "First"))
    assert repository.get("r1").name == "Renamed"

    assert repository.remove("r1").id == "r1"
    assert repository.get("r1") is None
    assert len(repository) == 0


def test_sqlite_container_persists_between_instances(tmp_path):
    path = str(tmp_path / "state.db")
    first = AppContainer(db_path=path)
    first.device_service.set_power("light", False)

    second = AppContainer(db_path=path)
    assert second.device_service.get_device("light").status == "OFF"
    assert len(second.room_service.list_rooms()) == 2

    second.reset()
    assert second.device_service.get_device("light").status == "ON"


def test_default_container_is_in_memory():
    container = get_container()
    assert not container.db_path
    assert len(container.device_service.list_devices()) == 3
