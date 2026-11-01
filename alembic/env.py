"""Explicit PostgreSQL migration target; no credentials in config or logs.

AI-GENERATED START: prepared with ChatGPT; verified on isolated PostgreSQL.
"""

from alembic import context
from sqlalchemy import create_engine, pool

from backend.app.core.config import get_database_url
from backend.app.db import models  # noqa: F401

options = context.get_x_argument(as_dictionary=True)
test_flag = options.get("test_db", "false").lower()
if test_flag not in {"true", "false"}:
    raise ValueError("test_db must be true or false")
url = get_database_url(test=test_flag == "true")

# Migrations remain explicit and reviewed; registering models does not enable
# unattended autogeneration or create tables during application imports.
if getattr(context.config.cmd_opts, "autogenerate", False):
    raise ValueError("Integrate all ORM models before enabling autogeneration")


def run_migrations():
    if context.is_offline_mode():
        context.configure(url=url, literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return

    supplied = context.config.attributes.get("connection")
    if supplied is not None:
        context.configure(connection=supplied)
        with context.begin_transaction():
            context.run_migrations()
        return

    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run_migrations()
# AI-GENERATED END
