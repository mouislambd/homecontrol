"""Abstract contracts used across the application.

Keeping the contracts here (and nowhere else) is what lets ``main`` depend on
abstractions rather than on concrete storage or device implementations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class SmartDevice(ABC):
    """Interface-like contract every smart device must satisfy."""

    @abstractmethod
    def turn_on(self) -> str:
        """Switch the device on and return a result message."""

    @abstractmethod
    def turn_off(self) -> str:
        """Switch the device off and return a result message."""


class Repository(ABC, Generic[T]):
    """Persistence-agnostic CRUD contract (Implementor in Bridge terms)."""

    @abstractmethod
    def add(self, item: T) -> T:
        """Store a new item and return it."""

    @abstractmethod
    def get(self, item_id: str) -> T | None:
        """Return an item by id or ``None``."""

    @abstractmethod
    def get_all(self) -> tuple[T, ...]:
        """Return an immutable snapshot of all items."""

    @abstractmethod
    def update(self, item: T) -> T:
        """Replace an existing item."""

    @abstractmethod
    def remove(self, item_id: str) -> T | None:
        """Delete and return an item, or ``None`` when absent."""


class EventPublisher(ABC):
    """Output boundary for domain events (Dependency Inversion)."""

    @abstractmethod
    def publish(self, event: object) -> None:
        """Publish an event to all subscribers."""
