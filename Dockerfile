FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="$HOME/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml ruff.toml .env.example ./
COPY . .

# Install dependencies (all phases included in Docker)
RUN uv pip install --system -e ".[all]"

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
