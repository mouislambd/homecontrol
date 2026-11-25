import pytest

from backend.controller import control_device
from backend.devices import AC, Fan, Light
from backend.interfaces import SmartDevice


@pytest.mark.parametrize("device_class", [Light, Fan, AC])
def test_device_turn_on_and_off(device_class):
    device = device_class()

    assert device.status == "OFF"
    assert control_device(device, True) == f"{device.name} is ON"
    assert device.status == "ON"
    assert control_device(device, True) == f"{device.name} is ON"
    assert control_device(device, False) == f"{device.name} is OFF"
    assert device.status == "OFF"
    assert control_device(device, False) == f"{device.name} is OFF"


def test_devices_keep_independent_statuses():
    light, fan, ac = Light(), Fan(), AC()

    control_device(light, True)
    control_device(fan, True)
    control_device(ac, True)
    control_device(fan, False)

    assert light.status == "ON"
    assert fan.status == "OFF"
    assert ac.status == "ON"


def test_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        SmartDevice()


def test_missing_abstract_method_cannot_be_instantiated():
    class IncompleteDevice(SmartDevice):
        def turn_on(self) -> str:
            return "on"

    with pytest.raises(TypeError):
        IncompleteDevice()


def test_polymorphism_through_common_control_function():
    devices: list[SmartDevice] = [Light(), Fan(), AC()]

    for device in devices:
        control_device(device, True)
    assert [device.status for device in devices] == ["ON", "ON", "ON"]

    for device in devices:
        control_device(device, False)
    assert [device.status for device in devices] == ["OFF", "OFF", "OFF"]
