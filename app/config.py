"""
Phase 1: Application Configuration

Load configuration from environment variables and config files.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import toml


@dataclass
class AppConfig:
    """
    Application configuration loaded from environment and TOML files.
    
    TODO: Implement configuration loading from:
    - .env file (via python-dotenv)
    - config/symbols.toml
    - Environment variables (override toml)
    """
    
    app_name: str = "de-bootcamp-summer2026"
    app_env: str = "development"
    duckdb_path: str = "data/app.duckdb"
    postgres_url: str = ""
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Load configuration from environment after initialization."""
        # TODO: Load from .env file
        # TODO: Override with environment variables
        # TODO: Load symbols from config/symbols.toml
        pass
    
    @property
    def symbols(self) -> list[str]:
        """Get list of market symbols to track."""
        # TODO: Load from config/symbols.toml
        # TODO: Return list like ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]
        return []
    
    @property
    def use_postgres(self) -> bool:
        """Check if PostgreSQL should be used instead of DuckDB."""
        # TODO: Return True if POSTGRES_URL is set
        return bool(self.postgres_url)
