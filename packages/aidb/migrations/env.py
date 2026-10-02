"""Alembic environment. Online mode only; run as the admin/owner role, never as app_user."""

from alembic import context
from sqlalchemy import create_engine

config = context.config

if context.is_offline_mode():
    raise RuntimeError("offline migrations are not supported (DDL uses DO blocks and roles)")

engine = create_engine(
    config.get_main_option("sqlalchemy.url"), connect_args={"client_encoding": "utf8"}
)
with engine.connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
