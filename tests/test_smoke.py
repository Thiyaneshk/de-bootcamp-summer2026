"""
Smoke Tests

Quick integration tests to verify basic functionality.

TODO: Implement tests:
- Test Streamlit app loads
- Test database connection
- Test yfinance API availability
- Test Docker services health
"""



def test_app_imports():
    """Test that app imports successfully."""
    from app.config import AppConfig
    from app.main import main
    assert main is not None
    assert AppConfig is not None


def test_config_loads():
    """Test that configuration loads."""
    from app.config import AppConfig
    config = AppConfig()
    assert config is not None
    assert config.app_env in ["development", "production", "testing"]


def test_db_accessible():
    """Test that database is accessible."""
    from app.db.connection import get_db_engine
    with get_db_engine() as engine:
        assert engine is not None
