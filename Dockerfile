FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/lists/*

# Install uv (fix: use absolute path, not $HOME which breaks at build time)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Copy dependency files first (layer cache optimisation)
COPY pyproject.toml ruff.toml ./

# Install Phase 1 dependencies (what Streamlit needs)
# Using pip directly for simplicity in Docker; uv available for dev
RUN pip install --no-cache-dir \
    streamlit>=1.40.0 \
    plotly>=6.6.0 \
    "yfinance>=0.2.40" \
    "duckdb>=1.0.0" \
    "sqlalchemy>=2.0.0" \
    "pandas>=2.0.0" \
    "numpy>=1.24.0" \
    psycopg2-binary \
    toml \
    python-dotenv \
    redis>=5.0.0

# Copy the full project
COPY . .

# Install the project package itself (app/, scripts/)
RUN pip install --no-cache-dir -e "." --no-deps

# Expose Streamlit
EXPOSE 8501

# Default: run Streamlit
CMD ["streamlit", "run", "app/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
