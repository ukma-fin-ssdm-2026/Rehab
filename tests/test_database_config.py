"""Configuration safety and lazy initialization for the shared database layer."""

import datetime as dt
import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest


def configure(monkeypatch, dev, test):
    monkeypatch.setenv("DATABASE_URL", dev)
    monkeypatch.setenv("TEST_DATABASE_URL", test)
    return importlib.import_module("backend.app.core.config")


def test_development_and_test_database_urls_are_selected_separately(monkeypatch):
    dev = "postgresql+psycopg://dev:password@127.0.0.1:25432/rehab_dev"
    test = "postgresql+psycopg://test:password@127.0.0.1:25433/rehab_test"
    config = configure(monkeypatch, dev, test)
    assert config.get_database_url() == dev
    assert config.get_database_url(test=True) == test


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_test_database_cannot_alias_development_with_different_credentials(
    monkeypatch, host
):
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:one@localhost:5432/rehab_test",
        f"postgresql+psycopg://other:two@{host}:5432/rehab_test",
    )
    with pytest.raises(ValueError, match="different"):
        config.get_database_url(test=True)


def test_test_database_must_have_explicit_test_name(monkeypatch):
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:secret@localhost:25432/rehab_dev",
        "postgresql+psycopg://test:secret@localhost:25433/production",
    )
    with pytest.raises(ValueError, match="_test"):
        config.get_database_url(test=True)


@pytest.mark.parametrize(
    "parameter", ["dbname", "host", "hostaddr", "port", "user", "service", "conninfo"]
)
def test_connection_query_cannot_override_validated_target(monkeypatch, parameter):
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:secret@localhost:25432/rehab_dev",
        f"postgresql+psycopg://test:secret@localhost:25433/rehab_test?{parameter}=rehab_dev",
    )
    with pytest.raises(ValueError, match="override"):
        config.get_database_url(test=True)


def test_same_database_name_is_rejected_even_with_different_host_aliases(monkeypatch):
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:secret@dev-alias:5432/rehab_test",
        "postgresql+psycopg://test:secret@another-alias:5432/rehab_test",
    )
    with pytest.raises(ValueError, match="different"):
        config.get_database_url(test=True)


def test_ssl_query_options_remain_supported(monkeypatch):
    test = "postgresql+psycopg://test:secret@localhost:25433/rehab_test?sslmode=require"
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:secret@localhost:25432/rehab_dev",
        test,
    )
    assert config.get_database_url(test=True) == test


def test_missing_test_url_does_not_fall_back_to_development(monkeypatch):
    config = configure(
        monkeypatch,
        "postgresql+psycopg://dev:secret@localhost:25432/rehab_dev",
        "",
    )
    with pytest.raises(ValueError, match="TEST_DATABASE_URL"):
        config.get_database_url(test=True)


def test_database_configuration_errors_do_not_reveal_passwords(monkeypatch):
    config = configure(monkeypatch, "sqlite:///private-password", "")
    with pytest.raises(ValueError) as error:
        config.get_database_url()
    assert "private-password" not in str(error.value)


def test_clock_uses_kyiv_calendar_day_at_utc_boundary(monkeypatch):
    clock = importlib.import_module("backend.app.core.clock")
    instant = dt.datetime(2026, 10, 29, 22, 30, tzinfo=dt.timezone.utc)
    monkeypatch.setattr(clock, "utc_now", lambda: instant)
    assert clock.today_local() == dt.date(2026, 10, 30)


def test_clock_returns_aware_utc_timestamp():
    clock = importlib.import_module("backend.app.core.clock")
    assert clock.utc_now().utcoffset() == dt.timedelta(0)


def test_importing_database_layer_and_openapi_requires_no_database():
    env = dict(os.environ, DATABASE_URL="", TEST_DATABASE_URL="")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import backend.app.db.session; "
            "from backend.app.main import app; "
            "assert app.openapi()['paths']; print('OK')",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_neon_plain_urls_get_the_psycopg_driver(monkeypatch, scheme):
    config = configure(
        monkeypatch,
        f"{scheme}://u:p@ep-x-pooler.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require",
        "",
    )
    assert config.get_database_url() == (
        "postgresql+psycopg://u:p@ep-x-pooler.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )


def test_migrations_prefer_direct_neon_connection(monkeypatch):
    config = configure(monkeypatch, "postgresql://u:p@ep-x-pooler.neon.tech/neondb", "")
    monkeypatch.setenv(
        "DATABASE_URL_UNPOOLED", "postgresql://u:p@ep-x.neon.tech/neondb"
    )
    assert config.get_migration_database_url() == (
        "postgresql+psycopg://u:p@ep-x.neon.tech/neondb"
    )


def test_migrations_fall_back_to_database_url(monkeypatch):
    dev = "postgresql+psycopg://dev:secret@localhost:25432/rehab_dev"
    config = configure(monkeypatch, dev, "")
    monkeypatch.delenv("DATABASE_URL_UNPOOLED", raising=False)
    assert config.get_migration_database_url() == dev


def test_neon_local_env_file_is_read_after_dot_env(monkeypatch, tmp_path):
    config = configure(monkeypatch, "", "")
    monkeypatch.delenv("DATABASE_URL")
    (tmp_path / ".env.local").write_text(
        "DATABASE_URL=postgresql://u:p@ep-x.neon.tech/neondb\n"
    )
    monkeypatch.setattr(
        config, "ENV_FILES", (tmp_path / ".env", tmp_path / ".env.local")
    )
    assert config.get_database_url() == "postgresql+psycopg://u:p@ep-x.neon.tech/neondb"


def test_pooled_neon_engine_disables_prepared_statements(monkeypatch):
    session = importlib.import_module("backend.app.db.session")
    calls = {}
    monkeypatch.setattr(
        session, "create_engine", lambda url, **kw: calls.setdefault(url, kw)
    )
    pooled = "postgresql+psycopg://u:p@ep-x-pooler.neon.tech/neondb"
    direct = "postgresql+psycopg://u:p@ep-x.neon.tech/neondb"
    session._engine_for_url.__wrapped__(pooled)
    session._engine_for_url.__wrapped__(direct)
    assert calls[pooled]["connect_args"]["prepare_threshold"] is None
    assert "prepare_threshold" not in calls[direct]["connect_args"]
