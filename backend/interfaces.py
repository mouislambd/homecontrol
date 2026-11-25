from abc import ABC, abstractmethod


class SmartDevice(ABC):
    """Interface-like contract every smart device must satisfy."""

    @abstractmethod
    def turn_on(self) -> str:
        """Switch the device on and return a result message."""

    @abstractmethod
    def turn_off(self) -> str:
        """Switch the device off and return a result message."""
