"""Opt-in PostgreSQL fixtures. Existing pure/prototype tests remain independent."""

from pathlib import Path
from types import SimpleNamespace

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_url

# Load real bindings before auth unit tests temporarily replace sys.modules.
# Import is connection-free; otherwise later SQL fixtures can inherit fake repos.
from backend.app.routers import auth as _auth_router  # noqa: F401

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
    from backend.app.db.models.user import User  # noqa: F401
    from backend.app.db.models.entry import DayRecord  # noqa: F401

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


@pytest.fixture
def authenticated_calendar(postgres_schema, calendar_db, monkeypatch):
    from fastapi import FastAPI, HTTPException
    from fastapi.exceptions import RequestValidationError
    from fastapi.testclient import TestClient
    from backend.app import security
    from backend.app.db.session import get_db
    from backend.app.main import http_exception_handler, validation_exception_handler
    from backend.app.routers import auth, calendar_postgres

    monkeypatch.setenv(
        "JWT_SECRET", "postgres-integration-test-secret-at-least-32-chars"
    )
    application = FastAPI()
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(calendar_postgres.router, prefix="/api/v1")

    def database():
        with Session(postgres_schema, expire_on_commit=False) as session:
            try:
                yield session
            except BaseException:
                session.rollback()
                raise

    # Override both explicit DB boundaries, never the authentication dependency.
    application.dependency_overrides[get_db] = database
    application.dependency_overrides[security._db_session] = database
    with TestClient(application) as client:
        yield client


@pytest.fixture
def registered_users(authenticated_calendar):
    password = "integration-password-123"
    accounts = []
    for name in ("first", "second"):
        email = f"{name}@integration.test"
        response = authenticated_calendar.post(
            "/api/v1/auth/register",
            json={"name": name, "nickname": name, "email": email, "password": password},
        )
        assert response.status_code == 201, response.text
        login = authenticated_calendar.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert login.status_code == 200, login.text
        accounts.append(
            (
                response.json(),
                {"Authorization": f"Bearer {login.json()['access_token']}"},
            )
        )
    return accounts


@pytest.fixture
def calendar_contract_api(authenticated_calendar):
    """Real SQL/auth; explicit progress double until Mariia's KT-1 module.

    This verifies calendar contracts, not real progress integration.
    """
    from backend.app.routers import calendar_postgres

    application = authenticated_calendar.app
    application.dependency_overrides[calendar_postgres.get_progress_sync] = (
        lambda: lambda db, user_id, today: None
    )
    try:
        yield authenticated_calendar
    finally:
        application.dependency_overrides.pop(calendar_postgres.get_progress_sync, None)


@pytest.fixture
def calendar_regression_data(calendar_contract_api, registered_users, calendar_db):
    """Historical/recent entries with real accounts and signed sessions."""
    import datetime as dt
    from backend.app.core.clock import today_local, utc_now
    from backend.app.db.models.entry import DayRecord
    from backend.app.db.models.user import User

    owner, headers = registered_users[0]
    _, second_headers = registered_users[1]
    calendar_db.get(User, owner["user_id"]).tracking_start_date = (
        today_local() - dt.timedelta(days=30)
    )
    old = DayRecord(
        user_id=owner["user_id"],
        date=today_local() - dt.timedelta(days=4),
        status="relapse",
        trigger_category="stress",
        drinks=[],
        created_at=utc_now() - dt.timedelta(days=5),
    )
    recent = DayRecord(
        user_id=owner["user_id"],
        date=today_local() - dt.timedelta(days=1),
        status="relapse",
        trigger_category="stress",
        drinks=[],
        created_at=utc_now() - dt.timedelta(hours=1),
    )
    calendar_db.add_all([old, recent])
    calendar_db.commit()
    return SimpleNamespace(
        client=calendar_contract_api,
        headers=headers,
        second_headers=second_headers,
        recent_id=recent.record_id,
        old_id=old.record_id,
        db=calendar_db,
    )
