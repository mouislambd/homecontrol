"""Thread-safe in-memory repository implementations.

Callers receive immutable snapshots, so the internal store cannot be mutated
from outside — a deliberate fix for the original module-global registry leak.
"""

from collections.abc import Callable
from threading import RLock
from typing import Generic, TypeVar

try:
    from .exceptions import ConflictError
    from .interfaces import Repository
except ImportError:
    from exceptions import ConflictError
    from interfaces import Repository

T = TypeVar("T")


class InMemoryRepository(Repository[T], Generic[T]):
    def __init__(
        self,
        key: Callable[[T], str],
        items: list[T] | tuple[T, ...] | None = None,
    ) -> None:
        self._key = key
        self._items: dict[str, T] = {}
        self._lock = RLock()
        for item in items or ():
            self._items[key(item)] = item

    def add(self, item: T) -> T:
        with self._lock:
            item_id = self._key(item)
            if item_id in self._items:
                raise ConflictError(f"Item '{item_id}' already exists")
            self._items[item_id] = item
            return item

    def get(self, item_id: str) -> T | None:
        with self._lock:
            return self._items.get(item_id)

    def get_all(self) -> tuple[T, ...]:
        with self._lock:
            return tuple(self._items.values())

    def update(self, item: T) -> T:
        with self._lock:
            item_id = self._key(item)
            if item_id not in self._items:
                raise ConflictError(f"Item '{item_id}' does not exist")
            self._items[item_id] = item
            return item

    def remove(self, item_id: str) -> T | None:
        with self._lock:
            return self._items.pop(item_id, None)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
