"""
schedule_pg_sync.py — Daily automated DuckDB → PostgreSQL sync

Runs forever, waking up each day at the specified time to:
  1. Download fresh data from yfinance
  2. Store in DuckDB
  3. Push to PostgreSQL

Usage:
    # Sync specific symbols at 08:00 every day
    uv run python -m scripts.schedule_pg_sync --time 08:00 --symbols AAPL,MSFT,ITC.NS

    # Sync all symbols from config/symbols.toml at 09:30 every day
    uv run python -m scripts.schedule_pg_sync --time 09:30 --all

    # Run once immediately (useful for testing)
    uv run python -m scripts.schedule_pg_sync --now --symbols AAPL,MSFT

Environment variables (via .env):
    POSTGRES_URL   — PostgreSQL connection string (required)
    DUCKDB_PATH    — Path to DuckDB file (default: data/app.duckdb)

Notes:
    - Runs in foreground; use screen / tmux / launchd / cron to keep it alive.
    - For production scheduling with Airflow, see airflow/dags/etl_prices_dag.py.
"""

import argparse
import logging
import os
import signal
import time
from datetime import datetime, timedelta

# ── Logging setup ─────────────────────────────────────────────────────────────

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("schedule_pg_sync")


# ── .env loader (optional) ────────────────────────────────────────────────────

def _load_dotenv() -> None:
    """Load .env file into os.environ if python-dotenv is available."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logger.info("Loaded .env from %s", env_path)
    except ImportError:
        # python-dotenv not installed — parse manually
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())


# ── Scheduling helpers ────────────────────────────────────────────────────────

def _seconds_until(target_time_str: str) -> float:
    """Return seconds until the next occurrence of HH:MM today (or tomorrow)."""
    now = datetime.now()
    h, m = map(int, target_time_str.split(":"))
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_sync(symbols: list[str], use_all: bool, period: str) -> None:
    """Execute one sync cycle."""
    from scripts.pg_loader import sync_all_from_config, sync_symbols_to_postgres

    pg_url = os.getenv("POSTGRES_URL", "")
    if not pg_url:
        logger.error(
            "POSTGRES_URL is not set — cannot push to PostgreSQL.\n"
            "Set it in .env or export POSTGRES_URL=postgresql+psycopg2://..."
        )
        return

    logger.info("=== Sync starting — %s ===", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        if use_all:
            result = sync_all_from_config(pg_url=pg_url, period=period)
        else:
            result = sync_symbols_to_postgres(symbols, pg_url=pg_url, period=period)

        logger.info(
            "=== Sync complete — yfinance rows: %d | PostgreSQL rows upserted: %d | errors: %d ===",
            result.get("yf_rows", 0),
            result.get("pg_rows", 0),
            len(result.get("errors", [])),
        )
        for err in result.get("errors", []):
            logger.error("  Error: %s", err)

    except Exception as e:
        logger.exception("Sync failed with unexpected error: %s", e)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Daily DuckDB → PostgreSQL price sync scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    sym_group = parser.add_mutually_exclusive_group(required=True)
    sym_group.add_argument(
        "--symbols",
        type=str,
        metavar="AAPL,MSFT,...",
        help="Comma-separated list of stock symbols to sync",
    )
    sym_group.add_argument(
        "--all",
        action="store_true",
        help="Sync all symbols defined in config/symbols.toml [default]",
    )

    parser.add_argument(
        "--time",
        type=str,
        default="08:00",
        metavar="HH:MM",
        help="Daily sync time in 24h format (default: 08:00)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="5d",
        metavar="PERIOD",
        help="yfinance period for fresh download (default: 5d)",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Run one sync immediately, then exit (useful for testing)",
    )

    return parser.parse_args(argv)


def main(argv=None) -> None:
    _load_dotenv()
    args = parse_args(argv)

    symbols: list[str] = []
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    # ── One-shot mode ─────────────────────────────────────────────────────────
    if args.now:
        logger.info("Running one-shot sync (--now flag)")
        _run_sync(symbols, use_all=args.all, period=args.period)
        return

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    _stop = False

    def _handle_signal(sig, frame):
        nonlocal _stop
        logger.info("Received signal %s — shutting down after current sleep", sig)
        _stop = True

    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # ── Scheduler loop ────────────────────────────────────────────────────────
    logger.info(
        "Scheduler started — daily sync at %s | symbols: %s",
        args.time,
        "ALL (symbols.toml)" if args.all else ", ".join(symbols),
    )
    logger.info("Press Ctrl+C to stop gracefully")

    while not _stop:
        wait_secs = _seconds_until(args.time)
        next_run = datetime.now() + timedelta(seconds=wait_secs)
        logger.info("Next sync at %s (in %.0f s)", next_run.strftime("%Y-%m-%d %H:%M:%S"), wait_secs)

        # Sleep in 60s chunks so we can respond to signals promptly
        slept = 0.0
        while slept < wait_secs and not _stop:
            chunk = min(60.0, wait_secs - slept)
            time.sleep(chunk)
            slept += chunk

        if _stop:
            break

        _run_sync(symbols, use_all=args.all, period=args.period)

    logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
