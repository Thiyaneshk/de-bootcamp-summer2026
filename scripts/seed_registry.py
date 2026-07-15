"""
Seed the Ticker Registry with initial instruments.

Includes major indices, ETFs, and stocks for India, Canada, and the US markets.
"""

from app.db.registry import add_instrument

def seed():
    instruments = [
        # Indian Market (NSE)
        {"symbol": "^NSEI", "name": "NIFTY 50", "exchange": "NSE", "instrument_type": "index"},
        {"symbol": "^NSEBANK", "name": "NIFTY BANK", "exchange": "NSE", "instrument_type": "index"},
        {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "exchange": "NSE", "instrument_type": "stock"},
        {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE", "instrument_type": "stock"},
        {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSE", "instrument_type": "stock"},
        {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "exchange": "NSE", "instrument_type": "stock"},
        {"symbol": "SBI.NS", "name": "State Bank of India", "exchange": "NSE", "instrument_type": "stock"},
        {"symbol": "NIFTYBEES.NS", "name": "Nippon India ETF Nifty 50 BeES", "exchange": "NSE", "instrument_type": "etf"},

        # Canadian Market (TSX)
        {"symbol": "^GSPTSE", "name": "S&P/TSX Composite Index", "exchange": "TSX", "instrument_type": "index"},
        {"symbol": "RY.TO", "name": "Royal Bank of Canada", "exchange": "TSX", "instrument_type": "stock"},
        {"symbol": "TD.TO", "name": "Toronto-Dominion Bank", "exchange": "TSX", "instrument_type": "stock"},
        {"symbol": "SHOP.TO", "name": "Shopify Inc.", "exchange": "TSX", "instrument_type": "stock"},
        {"symbol": "CNR.TO", "name": "Canadian National Railway", "exchange": "TSX", "instrument_type": "stock"},
        {"symbol": "ENB.TO", "name": "Enbridge Inc.", "exchange": "TSX", "instrument_type": "stock"},
        {"symbol": "XIU.TO", "name": "iShares S&P/TSX 60 Index ETF", "exchange": "TSX", "instrument_type": "etf"},

        # US Market (NYSE/NASDAQ)
        {"symbol": "^GSPC", "name": "S&P 500", "exchange": "NYSE", "instrument_type": "index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "NYSE", "instrument_type": "index"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "NASDAQ", "instrument_type": "index"},
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "instrument_type": "stock"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "instrument_type": "stock"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "instrument_type": "stock"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "instrument_type": "stock"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "instrument_type": "stock"},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "exchange": "NYSE", "instrument_type": "etf"},
        {"symbol": "QQQ", "name": "Invesco QQQ Trust", "exchange": "NASDAQ", "instrument_type": "etf"},
        {"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF Trust", "exchange": "NYSE", "instrument_type": "etf"},
    ]

    print("Seeding Ticker Registry...")
    for inst in instruments:
        try:
            add_instrument(**inst)
            print(f"Added {inst['symbol']} - {inst['name']} ({inst['instrument_type']})")
        except Exception as e:
            print(f"Error adding {inst['symbol']}: {e}")

    print("Seeding complete.")

if __name__ == "__main__":
    seed()
