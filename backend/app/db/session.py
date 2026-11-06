"""Lazy engine and one database session per request.

AI-GENERATED START: prepared with ChatGPT; transaction behavior tested.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url
from backend.app.errors import api_error


@lru_cache(maxsize=4)
def _engine_for_url(url: str) -> Engine:
    engine = create_engine(
        url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
        },
    )
    event.listen(engine, "begin", _set_transaction_limits)
    return engine


def _set_transaction_limits(connection) -> None:
    # SET LOCAL is transaction-scoped and works with Neon's transaction pooler.
    # Startup options or session-level SET are not safe for pooled Neon.
    # The job's autocommit advisory try-lock/unlock must stay outside a transaction.
    if connection.get_execution_options().get("isolation_level") == "AUTOCOMMIT":
        return
    connection.exec_driver_sql("SET LOCAL statement_timeout = '10s'")
    connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")


def get_engine() -> Engine:
    """Build the engine only when requested, not when app/OpenAPI imports."""
    return _engine_for_url(get_database_url())


def get_db() -> Iterator[Session]:
    """Routes explicitly commit; failure or forgotten commit cannot leak writes."""
    session = Session(get_engine(), expire_on_commit=False)
    try:
        yield session
    except OperationalError as exc:
        session.rollback()
        if getattr(exc.orig, "sqlstate", None) in {"57014", "55P03"}:
            raise api_error(
                503,
                "DATABASE_TIMEOUT",
                "База даних не відповіла вчасно. Перевірте стан операції перед повтором.",
            ) from exc
        raise
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


# AI-GENERATED END
