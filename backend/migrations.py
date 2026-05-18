import logging
import os
import subprocess
import sys

from sqlalchemy import inspect
from database import engine, Base

logger = logging.getLogger(__name__)

ALEMBIC_INI = os.path.join(os.path.dirname(__file__), "alembic.ini")


def _alembic_available() -> bool:
    return os.path.isdir(os.path.join(os.path.dirname(__file__), "alembic"))


def _run_alembic(*args) -> bool:
    if not _alembic_available():
        return False
    cmd = [sys.executable, "-m", "alembic", "-c", ALEMBIC_INI] + list(args)
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("Alembic command failed: %s", e.stderr or e.stdout)
        return False


def run_migrations():
    """Run migrations via Alembic if available; otherwise fall back to create_all()."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    is_fresh = "projects" not in existing_tables

    if is_fresh:
        logger.info("Fresh database detected. Using create_all() and stamping Alembic head.")
        Base.metadata.create_all(bind=engine)
        if _alembic_available():
            _run_alembic("stamp", "head")
            logger.info("Stamped database with current Alembic head.")
        return

    logger.info("Existing database detected. Running Alembic migrations.")
    if _run_alembic("upgrade", "head"):
        logger.info("Database migrated to head via Alembic.")
        return

    logger.warning("Alembic upgrade failed. Falling back to create_all() for any missing tables.")
    Base.metadata.create_all(bind=engine)
