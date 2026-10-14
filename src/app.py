import streamlit as st
from pathlib import Path
import tempfile
import uuid
import pandas as pd
import plotly.express as px
import plotly.io as pio

from langchain_core.messages import HumanMessage
from report_generator import generate_html_report
from chart_security import execute_chart_code
from security import (
    get_positive_int,
    render_login,
)

# Set default Plotly renderer to JSON for compatibility
pio.renderers.default = "json"

st.set_page_config(
    page_title="Agentic Data Science Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_login(st)

from graph import app as agent_app

st.markdown(
    """
    <style>
        .block-container { padding-top: 2.5rem; padding-bottom: 3rem; }
        .hero { padding: 1.25rem 1.5rem; border-radius: 16px; background: linear-gradient(135deg, #172554 0%, #1e3a8a 55%, #0f766e 100%); color: white; margin-bottom: 1.25rem; }
        .hero h1 { margin: 0; font-size: 2.15rem; letter-spacing: -0.03em; }
        .hero p { margin: 0.45rem 0 0; color: #dbeafe; font-size: 1rem; }
        .section-label { color: #64748b; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin: 1.25rem 0 0.4rem; }
        .stChatMessage { border-radius: 14px; }
        [data-testid="stMetric"] { background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem; border-radius: 12px; }
    </style>
    <div class="hero">
        <h1>Agentic Data Science Engine</h1>
        <p>Ask questions in plain English. Get verified SQL, interactive charts, and concise business insight.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize unique thread ID for LangGraph checkpointer if not present
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: Multi-file upload & Session Reset
with st.sidebar:
    st.markdown("## Workspace")
    st.caption("Configure your data workspace, then ask a question below.")
    st.markdown('<div class="section-label">1 · Data sources</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload CSV or Parquet files",
        type=["csv", "parquet"], 
        accept_multiple_files=True,
        help="Upload one or more files. The analyst can join them when the schemas allow it.",
    )
    
    file_paths = []
    if uploaded_files:
        max_upload_mb = get_positive_int("MAX_UPLOAD_SIZE_MB", 50)
        max_upload_files = get_positive_int("MAX_UPLOAD_FILES", 10)
        if len(uploaded_files) > max_upload_files:
            st.error(f"Upload at most {max_upload_files} files at a time.")
            st.stop()
        upload_dir = Path(tempfile.gettempdir()) / "agentic-ds-engine" / st.session_state.thread_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        for file in uploaded_files:
            if file.size > max_upload_mb * 1024 * 1024:
                st.error(f"{file.name} exceeds the {max_upload_mb} MB upload limit.")
                st.stop()
            file_path = upload_dir / Path(file.name).name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            file_paths.append(str(file_path))
        st.success(f"Loaded {len(file_paths)} file(s).")
        with st.expander("Preview loaded data", expanded=False):
            for file_path in file_paths:
                try:
                    preview = (
                        pd.read_parquet(file_path).head(5)
                        if file_path.lower().endswith(".parquet")
                        else pd.read_csv(file_path, nrows=5)
                    )
                    st.caption(Path(file_path).name)
                    st.dataframe(preview, use_container_width=True, hide_index=True)
                except Exception as exc:
                    st.caption(f"Preview unavailable: {exc}")
    else:
        file_paths = ["sample_sales.csv"]
        st.info("Using sample_sales.csv")

    st.markdown("---")
    st.markdown('<div class="section-label">2 · Session</div>', unsafe_allow_html=True)
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}`")
    if st.button("Reset Session / Clear Graph State", type="secondary", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.success("Session reset. Fresh graph thread initialized.")
        st.rerun()

    st.markdown("---")
    st.caption("Tip: Ask for trends, comparisons, rankings, outliers, or relationships between files.")
    if st.session_state.get("authenticated") and st.button("Sign out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

questions_asked = sum(1 for msg in st.session_state.messages if msg["role"] == "user")
metric_a, metric_b, metric_c = st.columns(3)
metric_a.metric("Questions asked", questions_asked)
metric_b.metric("Files in workspace", len(file_paths))
metric_c.metric("Query engine", "DuckDB")

# Display persistent chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "chart" in msg and msg["chart"] is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# User Query Input and Autonomous Execution
if user_input := st.chat_input("Ask a question about your data…"):
    # Display user input in UI and store in state
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Define initial state for graph execution with retry counter support
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "dataset_paths": file_paths,
        "sql_query": "",
        "query_result": "",
        "chart_code": "",
        "chart_evaluated": False,
        "is_approved": True,
        "retry_count": 0,
        "next_node": "",
        "status": "started"
    }

    with st.chat_message("assistant"):
        status_box = st.status("Autonomous agents executing analysis...", expanded=True)
        
        executed_sql = ""
        query_result = ""
        chart_code = ""
        final_response = ""
        
        # Stream graph nodes autonomously to completion
        for output in agent_app.stream(initial_state, config=config):
            for node_name, state_update in output.items():
                if node_name == "analyst":
                    executed_sql = state_update.get("sql_query", "")
                    retries = state_update.get("retry_count", 0)
                    if retries > 0:
                        status_box.write(f"Analyst node: Attempting auto-correction fix (Attempt #{retries})...")
                    else:
                        status_box.write("Analyst node: Generated SQL query.")
                    
                elif node_name == "sql_runner":
                    query_result = state_update.get("query_result", "")
                    if "SQL Execution Error" in query_result or "Error:" in query_result:
                        status_box.write("SQL Runner node: Execution error detected. Triggering self-healing loop...")
                    else:
                        status_box.write("SQL Runner node: Executed query successfully.")
                    
                elif node_name == "visualizer":
                    chart_code = state_update.get("chart_code", "")
                    if chart_code:
                        status_box.write("Visualizer node: Generated Plotly code.")
                    else:
                        status_box.write("Visualizer node: Data evaluated (no chart needed or skipped).")
                        
                elif node_name == "synthesizer":
                    raw_msg = state_update.get("messages", [])[-1].content
                    final_response = raw_msg.replace("Final Answer: ", "")
                    status_box.write("Synthesizer node: Generated executive summary.")

        status_box.update(label="Analysis Complete", state="complete", expanded=False)
        
        fig_obj = None
        if chart_code:
            try:
                fig_obj = execute_chart_code(chart_code)
            except Exception as e:
                st.caption(f"Chart execution failed: {e}")

        # Present the result as a compact, scannable analysis workspace.
        st.markdown("### Analysis result")
        summary_tab, data_tab, chart_tab = st.tabs(["Executive summary", "SQL & data", "Visualization"])
        with summary_tab:
            st.markdown(final_response or "No summary was generated.")
        with data_tab:
            if executed_sql:
                st.caption("Generated DuckDB SQL")
                st.code(executed_sql, language="sql")
            if query_result:
                st.caption("Query result")
                st.markdown(query_result)
        with chart_tab:
            if fig_obj is not None:
                st.plotly_chart(fig_obj, use_container_width=True)
            else:
                st.info("This result was not suitable for a chart.")

        report_html = generate_html_report(
            user_input, executed_sql, query_result, final_response, fig_obj
        )
        st.download_button(
            "Download HTML report",
            data=report_html,
            file_name="analysis-report.html",
            mime="text/html",
        )
        
        # Format structured message for persistent chat state
        full_history_content = (
            f"{final_response}\n\n"
            f"**Executed SQL Query:**\n```sql\n{executed_sql}\n```\n\n"
            f"**Query Results:**\n{query_result}"
        )
        
        # Persist assistant response and generated chart figure
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_history_content,
            "chart": fig_obj
        })
