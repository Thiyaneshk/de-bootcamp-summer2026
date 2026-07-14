with open("README.md", "r") as f:
    content = f.read()

content = content.replace(
    "- **Phase 7:** Cloud Data Warehouse (Snowflake)",
    "- **Phase 7:** Cloud Data Warehouse (Snowflake)\n- **Phase 10:** Ticker Registry & Dynamic Airflow Task Mapping"
)

phase_7_text = "**Time:** 1.5 hours | **Start:** See `docs/PHASE_7_SNOWFLAKE.md`"
phase_10_text = "\n\n### ✅ Phase 10: Ticker Registry & Dynamic Airflow Task Mapping (Completed on: _______)\n- [ ] Create registry database tables\n- [ ] Build Streamlit UI to manage tickers\n- [ ] Refactor Airflow DAG to use dynamic task mapping (expand)\n\n**Time:** 1.5 hours | **Start:** See `docs/PHASE_10_REGISTRY.md`"

content = content.replace(phase_7_text, phase_7_text + phase_10_text)

docs_7_text = "- **[docs/PHASE_7_SNOWFLAKE.md](docs/PHASE_7_SNOWFLAKE.md)** — Cloud DW integration with Snowflake"
docs_10_text = "\n- **[docs/PHASE_10_REGISTRY.md](docs/PHASE_10_REGISTRY.md)** — Ticker Registry & Dynamic Airflow Tasks"

content = content.replace(docs_7_text, docs_7_text + docs_10_text)

with open("README.md", "w") as f:
    f.write(content)
