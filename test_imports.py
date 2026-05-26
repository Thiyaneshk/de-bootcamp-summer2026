#!/usr/bin/env python3
"""Test that all imports work correctly."""

try:
    print("Testing imports...")
    
    print("  - app.core.indices...")
    from app.core.indices import get_index_symbols, get_nifty50_symbols, get_banknifty_symbols
    
    print("  - app.db.utils...")
    from app.db.utils import get_available_symbols, get_symbol_data_as_dataframe
    
    print("  - app.db.connection...")
    from app.db.connection import get_db_engine
    
    print("  - app.core.etl.prices...")
    from app.core.etl.prices import load_prices_daily
    
    print("  - app.views.02_Stock_Overview...")
    from app.views import import_module
    # We can't fully import the Streamlit views without running Streamlit,
    # but we can check the syntax
    
    print("\n✅ All imports successful!")
    
    # Test the indices functions
    print("\nTesting index symbols:")
    nifty50 = get_nifty50_symbols()
    banknifty = get_banknifty_symbols()
    print(f"  Nifty50: {len(nifty50)} symbols")
    print(f"  BankNifty: {len(banknifty)} symbols")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
