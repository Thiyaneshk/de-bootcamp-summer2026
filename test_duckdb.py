import duckdb

conn = duckdb.connect(':memory:')
conn.execute("CREATE SCHEMA IF NOT EXISTS registry")
conn.execute("""
CREATE TABLE registry.instruments (
    id             INTEGER PRIMARY KEY,
    symbol         VARCHAR(20) NOT NULL UNIQUE,
    name           VARCHAR(200),
    instrument_type VARCHAR(20) NOT NULL,
    exchange       VARCHAR(20),
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMP DEFAULT NOW(),
    updated_at     TIMESTAMP DEFAULT NOW()
);
""")
print("Success")
