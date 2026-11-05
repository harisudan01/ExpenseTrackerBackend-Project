"""Apply the SQL files in /migrations, in name order.

Usage (from the ExpenseTrackerBackend folder):
    python -m app.database.migrate

Each file is written to be safe to re-run, so running this again is harmless.
"""
from pathlib import Path

from sqlalchemy import text

from app.database.connection import engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def main() -> None:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"No migrations found in {MIGRATIONS_DIR}")
        return

    for path in files:
        print(f"Applying {path.name} ...")
        with engine.begin() as conn:  # one transaction per file
            conn.execute(text(path.read_text(encoding="utf-8")))

    print("Done.")


if __name__ == "__main__":
    main()
