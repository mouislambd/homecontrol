try:
    from .interfaces import SmartDevice
except ImportError:
    from interfaces import SmartDevice


class Light(SmartDevice):
    device_id = "light"
    name = "Light"

    def __init__(self, initial_status: str = "OFF") -> None:
        self.status = initial_status

    def turn_on(self) -> str:
        self.status = "ON"
        return f"{self.name} is {self.status}"

    def turn_off(self) -> str:
        self.status = "OFF"
        return f"{self.name} is {self.status}"


class Fan(SmartDevice):
    device_id = "fan"
    name = "Fan"

    def __init__(self, initial_status: str = "OFF") -> None:
        self.status = initial_status

    def turn_on(self) -> str:
        self.status = "ON"
        return f"{self.name} is {self.status}"

    def turn_off(self) -> str:
        self.status = "OFF"
        return f"{self.name} is {self.status}"


class AC(SmartDevice):
    device_id = "ac"
    name = "Air Conditioner"

    def __init__(self, initial_status: str = "OFF") -> None:
        self.status = initial_status

    def turn_on(self) -> str:
        self.status = "ON"
        return f"{self.name} is {self.status}"

    def turn_off(self) -> str:
        self.status = "OFF"
        return f"{self.name} is {self.status}"


DEFAULT_STATUSES = {
    Light.device_id: "ON",
    Fan.device_id: "OFF",
    AC.device_id: "ON",
}


def create_devices() -> dict[str, SmartDevice]:
    return {
        Light.device_id: Light(DEFAULT_STATUSES[Light.device_id]),
        Fan.device_id: Fan(DEFAULT_STATUSES[Fan.device_id]),
        AC.device_id: AC(DEFAULT_STATUSES[AC.device_id]),
    }


_devices = create_devices()


def get_devices() -> dict[str, SmartDevice]:
    return _devices


def find_device(device_id: str) -> SmartDevice | None:
    return _devices.get(device_id)


def reset_devices() -> None:
    _devices.clear()
    _devices.update(create_devices())
