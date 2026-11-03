"""Read database configuration on demand, without exposing credentials.

AI-GENERATED START: prepared with ChatGPT; verified by configuration tests.
"""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def _value(name: str) -> str:
    if name in os.environ:
        return os.environ[name].strip()
    return (dotenv_values(ENV_FILE, interpolate=False).get(name) or "").strip()


def _parse(value: str, name: str):
    try:
        url = make_url(value)
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host
            and url.database
            and url.username
            and (url.port is None or 1 <= url.port <= 65535)
        )
    except (ArgumentError, ValueError):
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a PostgreSQL psycopg connection URL")
    # psycopg accepts query parameters that override the URL path/authority.
    # Validate exactly one source of identity before any test cleanup can run.
    overrides = {
        "dbname",
        "database",
        "host",
        "hostaddr",
        "port",
        "user",
        "password",
        "passfile",
        "service",
        "servicefile",
        "conninfo",
    }
    if any(key.lower() in overrides for key in url.query):
        raise ValueError(
            f"{name} cannot override connection identity in query parameters"
        )
    return url


def get_database_url(*, test: bool = False) -> str:
    """Select dev or explicitly isolated test PostgreSQL; never fall back."""
    name = "TEST_DATABASE_URL" if test else "DATABASE_URL"
    value = _value(name)
    url = _parse(value, name)
    if test:
        development = _parse(_value("DATABASE_URL"), "DATABASE_URL")
        if url.database == development.database:
            raise ValueError("Test and development database names must be different")
        if not url.database.endswith("_test"):
            raise ValueError("TEST_DATABASE_URL database name must end with _test")
    return value


# AI-GENERATED END
