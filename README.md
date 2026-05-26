# de-bootcamp-summer2026: Data Engineering Learning Project

A phased, hands-on learning project that progressively builds a complete data engineering stack. Learn one component at a time: from pulling financial data with Streamlit, to orchestrating ETL with Airflow, transforming data with dbt, and finally analyzing with LLM/RAG.

## 🎯 Project Overview

This is a **learning-first scaffold** designed to teach you modern data engineering concepts through practical implementation. Each phase builds on the previous one, so you can stop at any point and have a fully functional system.

### What You'll Learn

- **Phase 1:** Streamlit UI + yfinance data loading (DuckDB local storage)
- **Phase 2:** Airflow orchestration + PostgreSQL data warehouse setup
- **Phase 3:** dbt data transformations and modeling
- **Phase 4:** Analytics dashboards and SQL insights
- **Phase 5:** LLM integration + RAG-based analysis (optional)

---

## 📦 Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | ≥3.11 |
| **Package Manager** | uv | latest |
| **UI Framework** | Streamlit | ≥1.40.0 |
| **Data Source** | yfinance | ≥0.2.40 |
| **Analytics DB (Phase 1)** | DuckDB | ≥1.0.0 |
| **Data Warehouse (Phase 2)** | PostgreSQL | 15 |
| **Orchestration** | Apache Airflow | 2.10.2 |
| **Transformations** | dbt | 1.9.0+ |
| **Visualization** | Plotly | ≥6.6.0 |
| **LLM (Phase 5)** | Ollama | latest |
| **Code Quality** | Ruff + Black | latest |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://astral.sh/uv/) (fast Python package manager)
- Docker & Docker Compose (for Phase 2+)
- Git

### Phase 1: Local Streamlit (5 minutes)

```bash
# 1. Clone and navigate
git clone <repo-url>
cd de-bootcamp-summer2026

# 2. Install dependencies (Phase 1 only)
uv sync --extra phase1

# 3. Run the app
uv run streamlit run app/main.py

# Visit: http://localhost:8501
```

See **[SETUP_COMMANDS.md](SETUP_COMMANDS.md)** for complete Phase 1-5 setup.

---

## 📁 Project Structure

```
de-bootcamp-summer2026/
├── app/                      # Phase 1: Streamlit UI
│   ├── main.py               # Multi-page entry point
│   ├── config.py             # Configuration loading
│   ├── core/etl/prices.py    # yfinance wrapper
│   ├── db/                   # Database abstraction (DuckDB/PostgreSQL)
│   └── views/                # Streamlit pages (6 pages)
│
├── airflow/                  # Phase 2: DAG orchestration
│   └── dags/etl_prices_dag.py
│
├── dbt/                      # Phase 3: Data transformations
│   ├── models/staging/       # Data cleaning layer
│   └── models/marts/         # Analytics layer
│
├── config/
│   └── symbols.toml          # Market symbols configuration
│
├── scripts/                  # Utility scripts
│   ├── refresh_data.py       # ETL CLI entry
│   ├── init_db.py            # Database schema initialization
│   └── init_ollama.sh        # LLM setup
│
├── docs/                     # Phase-specific documentation
│   ├── PHASE_1_STREAMLIT.md
│   ├── PHASE_2_AIRFLOW_POSTGRES.md
│   ├── PHASE_3_DBT.md
│   ├── PHASE_4_ANALYTICS.md
│   └── PHASE_5_LLM_RAG.md
│
├── tests/                    # Test placeholders
├── data/                     # Local data storage (Phase 1)
├── Dockerfile               # Container definition
├── docker-compose.yml       # Services: PostgreSQL, Ollama, Streamlit
├── pyproject.toml           # Dependencies (phase-grouped)
├── ruff.toml               # Code linting config
└── SETUP_COMMANDS.md       # All setup commands (phases 0-5)
```

---

## 📚 Learning Path

### ✅ Phase 1: Streamlit + yfinance (Completed on: _______)
- [ ] Pull financial data from yfinance
- [ ] Store locally in DuckDB
- [ ] Display in Streamlit UI
- [ ] Explore raw data tables

**Time:** 1-2 hours | **Entry:** `uv run streamlit run app/main.py`

### ✅ Phase 2: Airflow + PostgreSQL (Completed on: _______)
- [ ] Set up PostgreSQL with Docker
- [ ] Create Airflow DAG for scheduled data ingestion
- [ ] Initialize database schema
- [ ] Store historical data

**Time:** 2-3 hours | **Start:** See `docs/PHASE_2_AIRFLOW_POSTGRES.md`

### ✅ Phase 3: dbt Transformations (Completed on: _______)
- [ ] Set up dbt project
- [ ] Create staging models (data cleaning)
- [ ] Create marts (aggregations, indicators)
- [ ] Run dbt tests

**Time:** 2-3 hours | **Start:** See `docs/PHASE_3_DBT.md`

### ✅ Phase 4: Analytics (Completed on: _______)
- [ ] Create analytics dashboards
- [ ] Query dbt marts with SQL
- [ ] Visualize insights with Plotly

**Time:** 1-2 hours | **Start:** See `docs/PHASE_4_ANALYTICS.md`

### ✅ Phase 5: LLM + RAG (Completed on: _______)
- [ ] Set up Ollama with local LLM
- [ ] Implement RAG-based chat analysis
- [ ] Connect to data insights

**Time:** 2-3 hours | **Start:** See `docs/PHASE_5_LLM_RAG.md`

---

## 📖 Documentation

> **📊 [PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** — **START HERE!** Current implementation progress, completion percentages, and pending tasks across all phases. Updated regularly to track progress.

- **[SETUP_COMMANDS.md](SETUP_COMMANDS.md)** — Every command from repo creation through Phase 5
- **[docs/PHASE_1_STREAMLIT.md](docs/PHASE_1_STREAMLIT.md)** — yfinance API, DuckDB storage
- **[docs/PHASE_2_AIRFLOW_POSTGRES.md](docs/PHASE_2_AIRFLOW_POSTGRES.md)** — DAG structure, schema design
- **[docs/PHASE_3_DBT.md](docs/PHASE_3_DBT.md)** — Model development, testing
- **[docs/PHASE_4_ANALYTICS.md](docs/PHASE_4_ANALYTICS.md)** — SQL queries, visualization
- **[docs/PHASE_5_LLM_RAG.md](docs/PHASE_5_LLM_RAG.md)** — Ollama setup, RAG patterns

---

## 🛠️ Configuration

### Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings (PostgreSQL URL for Phase 2+, Ollama URL for Phase 5, etc.)

### Market Symbols

Edit `config/symbols.toml` to customize which stock symbols to track:

```toml
[default]
symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]
interval = "5m"
period = "5d"
```

---

## 🐳 Docker Support

### Run Everything with Docker Compose

```bash
# Phase 1 (Streamlit only)
docker-compose up streamlit

# Phase 2+ (Streamlit + PostgreSQL)
docker-compose up

# Phase 5 (with Ollama)
docker-compose up --profile phase5

# Stop services
docker-compose down
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov=scripts

# Run specific test file
pytest tests/test_etl.py -v
```

---

## ❓ FAQ

**Q: Do I need to complete all phases?**  
A: No! Each phase is independent. You can stop at Phase 1 (Streamlit) or Phase 3 (with dbt) and have a complete system.

**Q: Can I use PostgreSQL from the start?**  
A: Yes, set `POSTGRES_URL` in `.env` before Phase 1. The app automatically switches to PostgreSQL if the env var is set.

**Q: How do I add more yfinance symbols?**  
A: Edit `config/symbols.toml` and restart the app.

**Q: What if I get database errors?**  
A: Phase 1 uses DuckDB (no setup needed). For PostgreSQL errors (Phase 2+), check the `SETUP_COMMANDS.md` database initialization section.

---

## 🤝 Learning Resources

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Apache Airflow Guide](https://airflow.apache.org/)
- [dbt Documentation](https://docs.getdbt.com/)
- [PostgreSQL Tutorials](https://www.postgresql.org/docs/15/)
- [Ollama Models](https://ollama.ai/)

---

## 📝 Notes

- This is a **learning project**, not production-ready code
- All Python files have minimal docstrings for you to fill in
- Each phase builds naturally on the previous one
- Estimated total time: 8-15 hours (2-3 hours per phase)

---

## 📄 License

MIT (or your preferred license)

---

**Created:** May 2026  
**Learning Goal:** Master modern data engineering stack through hands-on practice  
**Next Step:** Start with Phase 1 → See [SETUP_COMMANDS.md](SETUP_COMMANDS.md)
