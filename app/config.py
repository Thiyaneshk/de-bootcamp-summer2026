"""
Phase 1: Application Configuration

Load configuration from environment variables and config files.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import toml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class AppConfig:
    """
    Application configuration loaded from environment and TOML files.
    """

    app_name: str = "de-bootcamp-summer2026"
    app_env: str = "development"
    duckdb_path: str = "data/app.duckdb"
    postgres_url: str = ""
    log_level: str = "INFO"

    def __post_init__(self):
        """Load configuration from environment after initialization."""
        self.app_env = os.getenv("APP_ENV", self.app_env)
        self.duckdb_path = os.getenv("DUCKDB_PATH", self.duckdb_path)
        self.postgres_url = os.getenv("POSTGRES_URL", self.postgres_url)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)

    @property
    def symbols(self) -> list[str]:
        """Get list of market symbols to track from the registry or symbols.toml fallback."""
        try:
            from app.db.registry import get_active_symbols

            active_symbols = get_active_symbols()
            if active_symbols:
                return active_symbols
        except Exception:
            pass

        try:
            # Locate symbols.toml in parent project directory config folder
            project_root = Path(__file__).parent.parent
            toml_path = project_root / "config" / "symbols.toml"
            if toml_path.exists():
                config_data = toml.load(toml_path)
                return config_data.get("default", {}).get("symbols", [])
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to load symbols from symbols.toml: %s", e
            )

        # Fallback list if symbols.toml can't be read
        return ["AAPL", "MSFT", "ITC.NS", "LUPIN.NS"]

    @property
    def use_postgres(self) -> bool:
        """Check if PostgreSQL should be used instead of DuckDB."""
        return bool(self.postgres_url)
