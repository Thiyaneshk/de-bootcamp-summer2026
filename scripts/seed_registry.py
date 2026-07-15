"""Seed the ticker registry from a checked-in CSV data file."""

from __future__ import annotations

import csv
from pathlib import Path

from app.db.registry import add_instrument, init_registry_tables

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "ticker_registry_seed.csv"


def load_seed_instruments() -> list[dict[str, str]]:
    """Load instruments from the repository CSV seed file."""
    with DATA_FILE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            {
                "symbol": row["symbol"],
                "name": row["name"],
                "instrument_type": row["instrument_type"],
                "exchange": row["exchange"],
                "is_active": row.get("is_active", "true").lower() == "true",
            }
            for row in reader
        ]


def seed() -> dict[str, int]:
    """Seed the registry and return a simple summary for tests and CI."""
    init_registry_tables()
    print("Seeding Ticker Registry...")

    instruments = load_seed_instruments()

    inserted = 0
    errors = 0
    for inst in instruments:
        try:
            add_instrument(**inst)
            inserted += 1
            print(f"Added {inst['symbol']} - {inst['name']} ({inst['instrument_type']})")
        except Exception as exc:  # pragma: no cover - defensive logging
            errors += 1
            print(f"Error adding {inst['symbol']}: {exc}")

    print(f"Seeding complete. Added {inserted}/{len(instruments)} instruments.")
    return {"inserted": inserted, "errors": errors, "total": len(instruments)}


if __name__ == "__main__":
    seed()
