"""
Phase 1: Home Dashboard

Landing page showing project status, learning roadmap, quick stats,
and navigation guidance based on current repo implementation state.
"""

from datetime import date

import streamlit as st

# ── Phase / task definitions ────────────────────────────────────────────────

PHASES = [
    {
        "id": 1,
        "title": "Phase 1: Streamlit + yfinance",
        "icon": "📊",
        "time": "1–2 hours",
        "tech": "Python · Streamlit · yfinance · DuckDB · Plotly",
        "nav_page": "Stock Overview",
        "status": "completed",   # completed | in_progress | not_started
        "tasks": [
            ("Pull financial data from yfinance", True),
            ("ETL wrapper functions (load_prices_daily, load_prices_5m)", True),
            ("Multi-symbol downloader", True),
            ("Candlestick chart on Stock Overview page", True),
            ("Home Dashboard content (this page)", True),
            ("Data Explorer – raw table, CSV export & PostgreSQL push", True),
            ("Admin panel – DB status & cache clear", True),
        ],
        "description": (
            "Core data pipeline: download OHLCV data from Yahoo Finance "
            "and display interactive candlestick charts in Streamlit."
        ),
    },
    {
        "id": 2,
        "title": "Phase 2: Airflow + PostgreSQL",
        "icon": "🔄",
        "time": "2–3 hours",
        "tech": "Apache Airflow · PostgreSQL · Docker Compose",
        "nav_page": None,
        "status": "completed",
        "tasks": [
            ("Docker Compose with PostgreSQL service", True),
            ("Airflow DAG scaffold (etl_prices_dag.py)", True),
            ("refresh_all / refresh_symbols callable", True),
            ("validate_data_loaded task", True),
            ("init_db.py – PostgreSQL schema creation", True),
            ("pg_loader.py – DuckDB → PostgreSQL ETL helper", True),
            ("schedule_pg_sync.py – daily sync scheduler", True),
            ("Airflow DAG: 4-task pipeline (download→DuckDB→PostgreSQL→validate)", True),
            ("Test Airflow scheduler end-to-end", True),
            ("Airflow UI connection verified", True),
        ],
        "description": (
            "Schedule daily ETL with Apache Airflow, store historical data "
            "in a PostgreSQL warehouse, and monitor pipelines via the Airflow UI."
        ),
    },
    {
        "id": 3,
        "title": "Phase 3: dbt Transformations",
        "icon": "🔧",
        "time": "2–3 hours",
        "tech": "dbt · Jinja2 SQL · PostgreSQL / DuckDB",
        "nav_page": "Indicators",
        "status": "completed",
        "tasks": [
            ("dbt project structure (dbt_project.yml, profiles.yml)", True),
            ("sources.yml definition", True),
            ("stg_prices.sql – clean + pct_change column", True),
            ("stg_prices.yml – column docs & not_null tests", True),
            ("fct_daily_prices.sql – OHLCV daily aggregation", True),
            ("fct_technical_indicators.sql – SMA 20 / 50 scaffold", True),
            ("Full RSI, MACD, Bollinger Bands implementation", True),
            ("dbt test suite passing", True),
            ("dbt docs generated", True),
        ],
        "description": (
            "Transform raw prices into analytics-ready tables using dbt: "
            "staging models for cleaning, mart models for daily aggregations "
            "and technical indicators."
        ),
    },
    {
        "id": 4,
        "title": "Phase 4: Analytics Dashboards",
        "icon": "📉",
        "time": "1–2 hours",
        "tech": "Plotly · Streamlit · SQL",
        "nav_page": "Analysis",
        "status": "completed",
        "tasks": [
            ("Analytics page UI scaffold", True),
            ("Query dbt marts from Streamlit", True),
            ("Performance metrics dashboard", True),
            ("Correlation analysis chart", True),
            ("Risk analysis visualizations", True),
        ],
        "description": (
            "Build rich analytics dashboards querying dbt mart tables – "
            "performance metrics, correlations, and risk analysis with Plotly."
        ),
    },
    {
        "id": 5,
        "title": "Phase 5: LLM + RAG",
        "icon": "🤖",
        "time": "2–3 hours",
        "tech": "Ollama · LangChain / RAG · Streamlit Chat",
        "nav_page": "Assistant Chat",
        "status": "completed",
        "tasks": [
            ("Ollama setup script (init_ollama.sh)", True),
            ("RAG module scaffold (app/core/rag/)", True),
            ("Chat interface UI", True),
            ("Context retrieval from price data", True),
            ("LLM-powered response generation", True),
        ],
        "description": (
            "Integrate a local LLM via Ollama and build a RAG-powered chat "
            "interface that analyses stock data and answers natural-language questions."
        ),
    },
]

STATUS_META = {
    "completed":    {"label": "✅ Completed",    "color": "#10b981", "bg": "#064e3b"},
    "in_progress":  {"label": "🔶 In Progress",  "color": "#f59e0b", "bg": "#451a03"},
    "not_started":  {"label": "⬜ Not Started",  "color": "#6b7280", "bg": "#1f2937"},
}

QUICK_LINKS = [
    ("📖 SETUP_COMMANDS.md",                  "SETUP_COMMANDS.md"),
    ("📄 Phase 1 Docs",                        "docs/PHASE_1_STREAMLIT.md"),
    ("📄 Phase 2 Docs (Airflow + Postgres)",   "docs/PHASE_2_AIRFLOW_POSTGRES.md"),
    ("🐳 Phase 2 Docker Setup Guide",          "docs/PHASE_2_DOCKER_AIRFLOW_SETUP.md"),
    ("📄 Phase 3 Docs",                        "docs/PHASE_3_DBT.md"),
    ("📄 Phase 4 Docs",                        "docs/PHASE_4_ANALYTICS.md"),
    ("📄 Phase 5 Docs",                        "docs/PHASE_5_LLM_RAG.md"),
]

TECH_STACK = [
    ("Python", "≥3.11"),
    ("Streamlit", "≥1.40.0"),
    ("yfinance", "≥0.2.40"),
    ("DuckDB", "≥1.0.0"),
    ("PostgreSQL", "15"),
    ("Airflow", "2.10.2"),
    ("dbt", "1.9.0+"),
    ("Plotly", "≥6.6.0"),
    ("Ollama", "latest"),
    ("uv", "latest"),
]

TRACKED_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "BTC-USD"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _progress_bar(done: int, total: int, color: str) -> str:
    pct = done / total if total else 0
    fill = int(pct * 100)
    return (
        f'<div style="background:#1f2937;border-radius:4px;height:8px;width:100%;margin:6px 0 2px">'
        f'<div style="background:{color};height:8px;border-radius:4px;width:{fill}%"></div>'
        f'</div>'
        f'<small style="color:{color}">{done}/{total} tasks · {fill}%</small>'
    )


def _phase_card(phase: dict) -> None:
    meta = STATUS_META[phase["status"]]
    done  = sum(1 for _, v in phase["tasks"] if v)
    total = len(phase["tasks"])

    with st.container():
        st.markdown(
            f"""
            <div style="
                background:linear-gradient(135deg,{meta['bg']} 0%,#111827 100%);
                border:1px solid {meta['color']}44;
                border-left:4px solid {meta['color']};
                border-radius:12px;
                padding:18px 20px 14px;
                margin-bottom:12px;
            ">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
                    <span style="font-size:1.1rem;font-weight:700;color:#f1f5f9">
                        {phase['icon']} {phase['title']}
                    </span>
                    <span style="
                        background:{meta['color']}22;
                        color:{meta['color']};
                        border:1px solid {meta['color']}55;
                        border-radius:20px;padding:2px 10px;font-size:0.78rem;font-weight:600
                    ">{meta['label']}</span>
                </div>
                <p style="color:#94a3b8;margin:6px 0 10px;font-size:0.87rem">{phase['description']}</p>
                <div style="color:#64748b;font-size:0.8rem;margin-bottom:8px">
                    🕐 {phase['time']} &nbsp;|&nbsp; 🛠 {phase['tech']}
                </div>
                {_progress_bar(done, total, meta['color'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Expandable task checklist
        with st.expander(f"Phase {phase['id']} tasks ({done}/{total})", expanded=False):
            for task_name, is_done in phase["tasks"]:
                icon = "✅" if is_done else "⬜"
                colour = "#d1fae5" if is_done else "#9ca3af"
                st.markdown(
                    f'<span style="color:{colour}">{icon} {task_name}</span>',
                    unsafe_allow_html=True,
                )


# ── Main page ────────────────────────────────────────────────────────────────

def main() -> None:
    """Home dashboard – project status and learning roadmap."""

    # ── Hero ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="
            background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);
            border:1px solid #6366f144;
            border-radius:16px;padding:32px 28px 24px;margin-bottom:28px;
        ">
            <h1 style="margin:0;font-size:2rem;color:#e2e8f0">
                📊 DE Bootcamp Summer 2026
            </h1>
            <p style="color:#94a3b8;margin:8px 0 16px;font-size:1.05rem">
                A phased, hands-on data engineering learning project — from raw yfinance data
                to a full Airflow + dbt + LLM analytics stack.
            </p>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
                <span style="background:#6366f122;color:#a5b4fc;border:1px solid #6366f155;border-radius:20px;padding:4px 14px;font-size:0.85rem">Python 3.11+</span>
                <span style="background:#0ea5e922;color:#7dd3fc;border:1px solid #0ea5e955;border-radius:20px;padding:4px 14px;font-size:0.85rem">Streamlit</span>
                <span style="background:#10b98122;color:#6ee7b7;border:1px solid #10b98155;border-radius:20px;padding:4px 14px;font-size:0.85rem">Airflow</span>
                <span style="background:#f59e0b22;color:#fcd34d;border:1px solid #f59e0b55;border-radius:20px;padding:4px 14px;font-size:0.85rem">dbt</span>
                <span style="background:#ec489922;color:#f9a8d4;border:1px solid #ec489955;border-radius:20px;padding:4px 14px;font-size:0.85rem">Ollama LLM</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Overall progress KPIs ───────────────────────────────────────────────
    all_tasks  = [(done) for ph in PHASES for _, done in ph["tasks"]]
    total_done = sum(all_tasks)
    total_all  = len(all_tasks)

    completed_phases   = sum(1 for ph in PHASES if ph["status"] == "completed")
    in_progress_phases = sum(1 for ph in PHASES if ph["status"] == "in_progress")
    not_started_phases = sum(1 for ph in PHASES if ph["status"] == "not_started")
    overall_pct        = int(total_done / total_all * 100) if total_all else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Overall Progress", f"{overall_pct}%", f"{total_done}/{total_all} tasks")
    with k2:
        st.metric("✅ Phases Done",     str(completed_phases))
    with k3:
        st.metric("🔶 In Progress",     str(in_progress_phases))
    with k4:
        st.metric("⬜ Not Started",     str(not_started_phases))
    with k5:
        st.metric("📅 Project Date",    "Summer 2026")

    st.divider()

    # ── Two-column layout: roadmap + right sidebar ──────────────────────────
    left, right = st.columns([2, 1], gap="large")

    with left:
        st.subheader("🗺️ Learning Roadmap")
        for phase in PHASES:
            _phase_card(phase)

    with right:
        # ── Quick start ────────────────────────────────────────────────────
        st.subheader("🚀 Quick Start")
        st.markdown(
            """
            <div style="background:#0f172a;border:1px solid #334155;border-radius:10px;padding:14px">
                <pre style="color:#86efac;font-size:0.78rem;margin:0;white-space:pre-wrap"># Phase 1 – run locally
uv sync --extra phase1
uv run streamlit run app/main.py

# Open → http://localhost:8501</pre>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Tracked symbols ────────────────────────────────────────────────
        st.subheader("📌 Tracked Symbols")
        cols = st.columns(3)
        colours = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#0ea5e9"]
        for i, sym in enumerate(TRACKED_SYMBOLS):
            with cols[i % 3]:
                st.markdown(
                    f'<div style="background:{colours[i]}22;border:1px solid {colours[i]}55;'
                    f'border-radius:8px;padding:6px 10px;margin-bottom:6px;'
                    f'color:{colours[i]};font-weight:700;font-size:0.9rem;text-align:center">'
                    f'{sym}</div>',
                    unsafe_allow_html=True,
                )
        st.caption("Edit config/symbols.toml to add more")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Tech stack table ───────────────────────────────────────────────
        st.subheader("🛠 Tech Stack")
        for tech, ver in TECH_STACK:
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(f"**{tech}**")
            with col_b:
                st.markdown(
                    f'<span style="color:#94a3b8;font-size:0.82rem">{ver}</span>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Docs & links ───────────────────────────────────────────────────
        st.subheader("📖 Docs & Links")
        for label, path in QUICK_LINKS:
            st.markdown(f"[{label}]({path})")

    st.divider()

    # ── Navigation guide ───────────────────────────────────────────────────
    st.subheader("🧭 Navigate the App")
    nav_cols = st.columns(3)
    nav_pages = [
        ("📈 Stock Overview",     "Phase 1 · Load & chart OHLCV data",         "✅ Ready"),
        ("🔍 Data Explorer",      "Phase 1 · Raw data tables & CSV export",     "✅ Ready"),
        ("📊 Indicators",         "Phase 3 · dbt-powered technical indicators", "🔶 Stub"),
        ("📉 Analysis",           "Phase 4 · Analytics dashboards",             "⬜ Pending"),
        ("🤖 Assistant Chat",     "Phase 5 · Local LLM / RAG analysis",         "⬜ Pending"),
        ("⚙️ Admin",              "Phase 1+ · DB status & data refresh",        "🔶 Stub"),
    ]
    for i, (title, desc, badge) in enumerate(nav_pages):
        with nav_cols[i % 3]:
            st.markdown(
                f"""
                <div style="
                    background:#1e293b;border:1px solid #334155;border-radius:10px;
                    padding:14px;margin-bottom:10px;
                ">
                    <div style="font-weight:700;color:#e2e8f0;margin-bottom:4px">{title}</div>
                    <div style="color:#64748b;font-size:0.82rem;margin-bottom:8px">{desc}</div>
                    <span style="font-size:0.78rem;color:#94a3b8">{badge}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Footer ─────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="text-align:center;color:#475569;font-size:0.82rem;margin-top:24px;padding-top:16px;border-top:1px solid #1e293b">
            de-bootcamp-summer2026 · Learning project · Created May 2026 ·
            Last viewed {date.today().strftime("%d %b %Y")}
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
