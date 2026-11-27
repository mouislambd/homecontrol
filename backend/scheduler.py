"""Background runner that applies due schedules without blocking requests."""

from threading import Event, Thread

try:
    from .services import ScheduleService
except ImportError:
    from services import ScheduleService


class ScheduleRunner:
    def __init__(self, service: ScheduleService, interval_seconds: float = 30.0) -> None:
        self._service = service
        self._interval = interval_seconds
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = Thread(
            target=self._loop, name="schedule-runner", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                self._service.run_due()
            except Exception:
                import logging

                logging.getLogger(__name__).exception("schedule runner failed")
