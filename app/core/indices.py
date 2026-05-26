"""
India Market Index Constituents

Provides hardcoded lists of stocks for Nifty50 and BankNifty indices.
TODO: Make this dynamic by fetching from financial data sources.
"""

import toml
import os
from pathlib import Path


def load_indices_config():
    """Load indices configuration from symbols.toml."""
    # Get the app directory and navigate to config
    app_dir = Path(__file__).parent.parent  # app/core/indices.py -> app/
    config_path = app_dir.parent / "config" / "symbols.toml"
    
    try:
        with open(config_path) as f:
            config = toml.load(f)
        return config.get("india_indices", {})
    except Exception:
        # Fallback to hardcoded values if toml loading fails
        return {
            "nifty50": [
                "RELIANCE.NS", "TCS.NS", "HDFC.NS", "INFY.NS", "LT.NS",
                "ICICIBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "ASIANPAINT.NS", "HINDUNILVR.NS",
                "SBILIFE.NS", "BAJAJFINSV.NS", "COTTONMART.NS", "DRREDDY.NS", "NTPC.NS",
                "GAIL.NS", "COALINDIA.NS", "POWERGRID.NS", "ONGC.NS", "IOC.NS",
                "ITC.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "WIPROTECH.NS", "TECHM.NS",
                "HCL.NS", "INFOSYS.NS", "WIPRO.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
                "M&M.NS", "HEROMOTOCO.NS", "SBIN.NS", "AXISBANK.NS", "BANKBARODA.NS",
                "INDUSIND.NS", "BAJAJFINSV.NS", "GODREJIND.NS", "HONEYWELL.NS", "NESTLEIND.NS"
            ],
            "banknifty": [
                "SBIN.NS", "ICICIBANK.NS", "HDFC.NS", "AXISBANK.NS", "KOTAK.NS",
                "INDUSIND.NS", "BANKBARODA.NS", "IDFCBANK.NS", "AUBANK.NS", "FEDERALBNK.NS",
                "HDFCBANK.NS", "IDBIBANK.NS", "UBIBANK.NS", "BANDHANBNK.NS", "YESBANK.NS"
            ]
        }


def get_nifty50_symbols():
    """Get list of Nifty50 stock symbols."""
    config = load_indices_config()
    return config.get("nifty50", [])


def get_banknifty_symbols():
    """Get list of BankNifty stock symbols."""
    config = load_indices_config()
    return config.get("banknifty", [])


def get_index_symbols(index_name: str) -> list[str]:
    """
    Get stock symbols for a specific index.
    
    Args:
        index_name: Index name ('nifty50' or 'banknifty')
    
    Returns:
        List of stock symbols
    """
    config = load_indices_config()
    return config.get(index_name.lower(), [])
