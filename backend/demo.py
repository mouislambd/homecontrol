try:
    from .controller import control_device
    from .devices import get_devices
except ImportError:
    from controller import control_device
    from devices import get_devices


def main() -> None:
    for device in get_devices().values():
        print(control_device(device, True))
    for device in get_devices().values():
        print(control_device(device, False))


if __name__ == "__main__":
    main()
