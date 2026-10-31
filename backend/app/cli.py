from __future__ import annotations

import argparse
import json
import logging

from app.core.config import get_settings
from app.db.session import SessionLocal, init_db
from app.services.data_import import DataImportService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def import_historical() -> None:
    init_db()
    settings = get_settings()
    db = SessionLocal()
    try:
        result = DataImportService(db, settings).import_historical()
        print(json.dumps(result, default=str, indent=2))
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="WindScope operational commands")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("import-historical", help="Import January 2026 Elexon FUELHH and WINDFOR data")
    args = parser.parse_args()
    if args.command == "import-historical":
        import_historical()
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
