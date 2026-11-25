try:
    from .interfaces import SmartDevice
except ImportError:
    from interfaces import SmartDevice


def control_device(device: SmartDevice, should_turn_on: bool) -> str:
    """Drive any SmartDevice through the shared interface (polymorphism)."""
    if should_turn_on:
        return device.turn_on()
    return device.turn_off()
