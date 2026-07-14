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


def test_chat_modules_import_without_ollama_package():
    """Test that chat modules import cleanly when ollama is unavailable."""
    import importlib
    import sys
    from unittest.mock import patch

    original_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "ollama":
            raise ModuleNotFoundError("No module named 'ollama'")
        return original_import(name, globals, locals, fromlist, level)

    with patch("builtins.__import__", side_effect=fake_import):
        sys.modules.pop("app.views.page_06_assistant_chat", None)
        sys.modules.pop("app.core.rag.chat_engine", None)
        sys.modules.pop("ollama", None)

        chat_page = importlib.import_module("app.views.page_06_assistant_chat")
        chat_engine = importlib.import_module("app.core.rag.chat_engine")

    assert chat_page is not None
    assert chat_engine is not None
