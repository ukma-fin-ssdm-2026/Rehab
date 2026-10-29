"""Opt-in PostgreSQL fixtures. Existing pure/prototype tests remain independent."""

from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import Table, create_engine, text
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def postgres_engine():
    """Guard the target before opening any connection or changing schema."""
    url = get_database_url(test=True)
    engine = create_engine(url, connect_args={"connect_timeout": 5})
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def postgres_schema(postgres_engine):
    config = Config(str(ROOT / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(x=["test_db=true"])
    command.upgrade(config, "head")
    return postgres_engine


@pytest.fixture
def calendar_db(postgres_schema):
    """Clean only the explicitly guarded disposable test database."""
    from backend.app.db.base import Base
    from backend.app.db.models.entry import DayRecord  # noqa: F401

    # PR #172 owns User. Before it is integrated, reflect the real migrated
    # table for FK resolution instead of inventing a competing User model.
    if "users" not in Base.metadata.tables:
        Table("users", Base.metadata, autoload_with=postgres_schema)

    def clean():
        get_database_url(test=True)
        with postgres_schema.begin() as connection:
            connection.execute(
                text("TRUNCATE day_records, goals, users RESTART IDENTITY CASCADE")
            )

    clean()
    try:
        with Session(postgres_schema, expire_on_commit=False) as session:
            yield session
    finally:
        clean()


@pytest.fixture
def db_users(calendar_db):
    from backend.app.core.clock import today_local
    import datetime as dt

    ids = []
    for name in ("first", "second"):
        ids.append(
            calendar_db.scalar(
                text(
                    "INSERT INTO users "
                    "(email,name,nickname,password_hash,tracking_start_date) "
                    "VALUES (:email,:name,:name,'test-only-hash',:start) "
                    "RETURNING user_id"
                ),
                {
                    "email": f"{name}@example.test",
                    "name": name,
                    "start": today_local() - dt.timedelta(days=30),
                },
            )
        )
    calendar_db.commit()
    return ids
