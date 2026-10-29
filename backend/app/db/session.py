"""Lazy engine and one database session per request.

AI-GENERATED START: prepared with ChatGPT; transaction behavior tested.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url


@lru_cache(maxsize=4)
def _engine_for_url(url: str) -> Engine:
    connect_args = {"connect_timeout": 5}
    # Neon "-pooler" hosts run PgBouncer in transaction mode: avoid psycopg
    # server-side prepared statements that can outlive a pooled connection.
    if "-pooler" in (make_url(url).host or ""):
        connect_args["prepare_threshold"] = None
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_engine() -> Engine:
    """Build the engine only when requested, not when app/OpenAPI imports."""
    return _engine_for_url(get_database_url())


def get_db() -> Iterator[Session]:
    """Routes explicitly commit; failure or forgotten commit cannot leak writes."""
    session = Session(get_engine(), expire_on_commit=False)
    try:
        yield session
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


# AI-GENERATED END
