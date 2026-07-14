import os
import tempfile

import duckdb

from app.db.registry import (
    add_instrument,
    get_active_symbols,
    get_instruments,
    init_registry_tables,
    log_ingestion,
    set_instrument_active,
    upsert_index_constituents,
)


def test_registry_roundtrip_using_duckdb(tmp_path):
    db_path = tmp_path / "registry.duckdb"
    os.environ["DUCKDB_PATH"] = str(db_path)
    os.environ["POSTGRES_URL"] = ""

    with duckdb.connect(str(db_path)) as conn:
        init_registry_tables(conn)

    add_instrument("AAPL", name="Apple Inc.", instrument_type="stock", exchange="NASDAQ")
    add_instrument("^GSPC", name="S&P 500", instrument_type="index", exchange="INDEX")

    instruments = get_instruments()
    assert any(item["symbol"] == "AAPL" for item in instruments)
    assert any(item["symbol"] == "^GSPC" for item in instruments)

    upsert_index_constituents("^GSPC", [{"stock_symbol": "AAPL", "weight": 0.06}])
    constituents = get_instruments(instrument_type="stock")
    assert any(item["symbol"] == "AAPL" for item in constituents)

    set_instrument_active("AAPL", False)
    active_symbols = get_active_symbols()
    assert "AAPL" not in active_symbols

    log_ingestion("AAPL", "daily", "success", rows_ingested=10)
    history = log_ingestion("AAPL", "daily", "failed", rows_ingested=0)
    assert len(history) >= 1
