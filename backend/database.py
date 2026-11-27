"""Database configuration for the optional PostgreSQL backend.

Importing this module is safe when ``DATABASE_URL`` is absent: no engine or
connection is created at import time, so the existing in-memory application
keeps working exactly as before. Connection URLs and credentials are never
logged, and this module deliberately contains no models or migrations.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_PSYCOPG_DRIVER_PREFIX = "postgresql+psycopg://"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_current_session: ContextVar[Session | None] = ContextVar("current_db_session", default=None)


def _normalize_url(url: str) -> str:
    """Use the installed psycopg 3 driver for standard PostgreSQL URLs."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return f"{_PSYCOPG_DRIVER_PREFIX}{url[len(prefix):]}"
    return url


def database_url() -> str | None:
    """Read DATABASE_URL at call time so environment changes are honoured."""
    configured = os.getenv("DATABASE_URL", "").strip()
    return _normalize_url(configured) if configured else None


def is_database_configured() -> bool:
    return database_url() is not None


def get_engine() -> Engine:
    """Create and cache the engine on first use, never at import time."""
    global _engine
    if _engine is None:
        url = database_url()
        if url is None:
            raise RuntimeError(
                "DATABASE_URL is not set. Set it to enable PostgreSQL, or leave it "
                "unset to keep using the in-memory store."
            )
        _engine = create_engine(url, pool_pre_ping=True, echo=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Create and cache a session factory bound to the configured engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding one transaction-scoped session per request."""
    if not is_database_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        )

    session = get_session_factory()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide one session per operation, reusing an outer unit of work.

    Repositories call this for every operation. When a service wraps several
    writes in an outer ``session_scope()``, all of them share that session and
    commit atomically; otherwise each repository commits its own change.
    """
    existing = _current_session.get()
    if existing is not None:
        yield existing
        return

    session = get_session_factory()()
    token = _current_session.set(session)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        _current_session.reset(token)
        session.close()


def dispose_engine() -> None:
    """Release pooled connections and forget cached configuration."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
