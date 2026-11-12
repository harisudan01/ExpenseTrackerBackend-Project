"""Small start-up schema fixes for databases created by an older version of the app.

`Base.metadata.create_all` creates missing tables but never adds columns to existing ones,
so columns added later are added here (the same change as the matching file in /migrations).
"""
import logging

from sqlalchemy import Engine, inspect, text

logger = logging.getLogger("app.database")


def add_missing_columns(engine: Engine) -> None:
    try:
        inspector = inspect(engine)
        if not inspector.has_table("cashexpense_users"):
            return
        columns = {c["name"] for c in inspector.get_columns("cashexpense_users")}
        if "token_version" not in columns:
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE cashexpense_users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"
                ))
            logger.warning("Added the missing cashexpense_users.token_version column")
    except Exception:
        # e.g. the database user may not ALTER tables: apply migrations/003_add_token_version.sql by hand
        logger.exception(
            "Could not add cashexpense_users.token_version; run migrations/003_add_token_version.sql"
        )
