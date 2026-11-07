# db/migrate.py
"""
Run Alembic migrations on app startup.

Before migrations existed, tables were made with Base.metadata.create_all,
which creates missing tables but never adds columns to existing ones — so any
model change silently broke the live database. Startup now:

  1. Takes a Postgres advisory lock, so two instances starting at once don't
     both migrate.
  2. If the database has tables but no alembic_version (built by create_all),
     stamps it at the baseline revision, which matches that schema exactly.
  3. Upgrades to head.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from core.logger import get_logger

logger = get_logger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
BASELINE_REVISION = "0001_baseline"
# Arbitrary constant id for pg_advisory_lock — just has to be the same everywhere.
MIGRATION_LOCK_ID = 718_203_455


def _alembic_config(connection) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.attributes["connection"] = connection
    return cfg


def run_migrations(connection) -> None:
    """Synchronous; call via AsyncConnection.run_sync()."""
    is_postgres = connection.dialect.name == "postgresql"
    if is_postgres:
        connection.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
    try:
        cfg = _alembic_config(connection)
        tables = set(inspect(connection).get_table_names())
        if "alembic_version" not in tables and "users" in tables:
            logger.warning("migrations.stamping_existing_database revision=" + BASELINE_REVISION)
            command.stamp(cfg, BASELINE_REVISION)
        command.upgrade(cfg, "head")
        logger.info("migrations.up_to_date")
    finally:
        if is_postgres:
            connection.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
