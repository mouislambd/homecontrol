"""Concrete smart devices and the backward-compatible module registry.

The classes demonstrate inheritance from the ``SmartDevice`` abstraction,
while ``Device`` (in ``domain``) supplies validated state and a composed
``EnergyMeter``. ``control_device`` keeps driving them polymorphically.
"""

try:
    from .domain import BaseDevice, DeviceType
    from .interfaces import SmartDevice
except ImportError:
    from domain import BaseDevice, DeviceType
    from interfaces import SmartDevice


class Light(BaseDevice):
    device_id = "light"
    name = "Light"
    device_type = DeviceType.LIGHT

    def __init__(self, initial_status: str = "OFF") -> None:
        super().__init__(initial_status=initial_status, wattage=60.0)


class Fan(BaseDevice):
    device_id = "fan"
    name = "Fan"
    device_type = DeviceType.FAN

    def __init__(self, initial_status: str = "OFF") -> None:
        super().__init__(initial_status=initial_status, wattage=75.0)


class AC(BaseDevice):
    device_id = "ac"
    name = "Air Conditioner"
    device_type = DeviceType.AC

    def __init__(self, initial_status: str = "OFF") -> None:
        super().__init__(initial_status=initial_status, wattage=1200.0)


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
