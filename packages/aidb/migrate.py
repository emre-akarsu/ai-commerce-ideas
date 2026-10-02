"""Programmatic alembic runner (migrations are the only code allowed to run without a tenant)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from .session import make_engine, to_sa_url

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def alembic_config(url: str) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", to_sa_url(url).replace("%", "%%"))
    return cfg


def upgrade(url: str, revision: str = "head") -> None:
    command.upgrade(alembic_config(url), revision)


def downgrade(url: str, revision: str = "base") -> None:
    command.downgrade(alembic_config(url), revision)


def create_tenant(admin_url: str, tenant_id: str, name: str = "") -> None:
    """Provision a tenant. Admin/owner role only: app_user cannot insert into ``tenants``."""
    from sqlalchemy import text

    engine = make_engine(admin_url)
    try:
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO tenants (id, name) VALUES (:i, :n) ON CONFLICT DO NOTHING"),
                {"i": tenant_id, "n": name},
            )
    finally:
        engine.dispose()
