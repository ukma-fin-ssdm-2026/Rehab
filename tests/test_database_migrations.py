"""Run the real migration against the isolated PostgreSQL test container."""

from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

ROOT = Path(__file__).resolve().parents[1]


def upgrade():
    config = Config(str(ROOT / "alembic.ini"))
    config.cmd_opts = SimpleNamespace(x=["test_db=true"])
    command.upgrade(config, "head")


def test_initial_migration_creates_shared_postgresql_schema(postgres_engine):
    upgrade()
    inspector = inspect(postgres_engine)
    assert {"users", "day_records", "goals"} <= set(inspector.get_table_names())
    entry_columns = {c["name"]: c for c in inspector.get_columns("day_records")}
    assert str(entry_columns["drinks"]["type"]) == "JSONB"
    assert entry_columns["created_at"]["type"].timezone
    assert any(
        set(constraint["column_names"]) == {"user_id", "date"}
        for constraint in inspector.get_unique_constraints("day_records")
    )
    assert inspector.get_foreign_keys("day_records")[0]["referred_table"] == "users"
    assert inspector.get_foreign_keys("goals")[0]["referred_table"] == "users"
    assert inspector.get_columns("users")[0].get("identity") is not None


def test_repeating_upgrade_preserves_existing_rows(postgres_engine):
    upgrade()
    with postgres_engine.begin() as connection:
        user_id = connection.scalar(
            text(
                "INSERT INTO users "
                "(email,name,nickname,password_hash,tracking_start_date) "
                "VALUES ('migration-probe@example.test','Probe','probe','test-hash',"
                "CURRENT_DATE) RETURNING user_id"
            )
        )
    try:
        upgrade()
        with postgres_engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT nickname FROM users WHERE user_id=:id"),
                    {"id": user_id},
                )
                == "probe"
            )
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM users WHERE user_id=:id"), {"id": user_id}
            )


def test_database_enforces_calendar_uniqueness_and_goal_range(postgres_engine):
    upgrade()
    with postgres_engine.begin() as connection:
        user_id = connection.scalar(
            text(
                "INSERT INTO users "
                "(email,name,nickname,password_hash,tracking_start_date) "
                "VALUES ('constraint-probe@example.test','Probe','probe','test-hash',"
                "CURRENT_DATE) RETURNING user_id"
            )
        )
        connection.execute(
            text(
                "INSERT INTO day_records(user_id,date,status) VALUES (:id,CURRENT_DATE,'sober')"
            ),
            {"id": user_id},
        )
    try:
        with pytest.raises(IntegrityError):
            with postgres_engine.begin() as connection:
                connection.execute(
                    text(
                        "INSERT INTO day_records(user_id,date,status) VALUES (:id,CURRENT_DATE,'sober')"
                    ),
                    {"id": user_id},
                )
        with pytest.raises(IntegrityError):
            with postgres_engine.begin() as connection:
                connection.execute(
                    text("INSERT INTO goals(user_id,target_days) VALUES (:id,0)"),
                    {"id": user_id},
                )
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                text("DELETE FROM users WHERE user_id=:id"), {"id": user_id}
            )
