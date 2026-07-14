with open("airflow/dags/etl_prices_dag.py", "r") as f:
    content = f.read()

# Fix get_postgres_engine import
content = content.replace(
    "from app.db.connection import get_duckdb_connection, get_postgres_engine",
    "from app.db.connection import get_duckdb_connection, get_db_engine"
)

# Use get_db_engine to get postgres engine instead of missing get_postgres_engine
content = content.replace(
    "with get_postgres_engine() as engine:",
    "with get_db_engine() as engine:"
)

# Fix lambda and replace with a standard function for expand()
content = content.replace(
    ").expand(op_args=t1_active_symbols.output.map(lambda s: [s]))",
    ").expand(op_args=t1_active_symbols.output.map(list_wrap))"
)

# Add list_wrap definition
import_os_idx = content.find("import os")
content = content[:import_os_idx] + "def list_wrap(x):\n    return [x]\n\n" + content[import_os_idx:]

# Fix SQL injection and table name parsing for Postgres temp table
import re
# Replace: table_name = f"prices_etl_tmp_{symbol.replace('-','_')}"
content = re.sub(
    r'table_name = f"prices_etl_tmp_\{symbol.replace\([^)]+\)\}"',
    r'''
                    import re
                    clean_sym = re.sub(r'[^a-zA-Z0-9_]', '_', symbol).lower()
                    table_name = f"prices_etl_tmp_{clean_sym}"
    ''',
    content
)

# Put quotes around table_name
content = content.replace(
    "FROM {table_name}",
    'FROM "{table_name}"'
)
content = content.replace(
    "DROP TABLE IF EXISTS {table_name}",
    'DROP TABLE IF EXISTS "{table_name}"'
)

with open("airflow/dags/etl_prices_dag.py", "w") as f:
    f.write(content)
