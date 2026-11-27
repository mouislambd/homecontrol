"""Domain events, subscriptions and publisher implementations.

Services publish facts; history, notifications and automations subscribe.
This Observer-style wiring keeps those reactions out of the request path and
out of ``DeviceService`` itself.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from threading import RLock
from typing import Any

try:
    from .domain import utcnow
    from .interfaces import EventPublisher
except ImportError:
    from domain import utcnow
    from interfaces import EventPublisher

logger = logging.getLogger(__name__)

EventHandler = Callable[["DomainEvent"], None]


@dataclass(frozen=True)
class DomainEvent:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=utcnow)


class NoopEventPublisher(EventPublisher):
    """Null object: discards events when observability is not needed."""

    def publish(self, event: object) -> None:
        return None


class EventBroker(EventPublisher):
    """Thread-safe in-process broker with topic subscriptions and a log."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._events: list[DomainEvent] = []
        self._lock = RLock()

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        with self._lock:
            self._subscribers.setdefault(topic, []).append(handler)

    def publish(self, event: object) -> None:
        if not isinstance(event, DomainEvent):
            return
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._subscribers.get(event.topic, ()))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("event handler failed for topic=%s", event.topic)

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def clear_subscribers(self) -> None:
        with self._lock:
            self._subscribers.clear()

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._subscribers.clear()


InMemoryEventPublisher = EventBroker
