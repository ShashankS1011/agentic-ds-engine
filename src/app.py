import streamlit as st
import os
import uuid
import pandas as pd
import plotly.express as px
import plotly.io as pio

from langchain_core.messages import HumanMessage
from graph import app as agent_app

# Set default Plotly renderer to JSON for compatibility
pio.renderers.default = "json"

st.set_page_config(page_title="Agentic Data Science Engine", layout="wide")

st.title("Agentic Data Science Engine")
st.caption("Powered by LangGraph, DuckDB, and Groq")

# Initialize unique thread ID for LangGraph checkpointer if not present
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: Multi-file upload & Session Reset
with st.sidebar:
    st.header("1. Upload Datasets")
    uploaded_files = st.file_uploader(
        "Upload CSV or Parquet files", 
        type=["csv", "parquet"], 
        accept_multiple_files=True
    )
    
    file_paths = []
    if uploaded_files:
        for file in uploaded_files:
            file_path = file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            file_paths.append(file_path)
        st.success(f"Loaded {len(file_paths)} file(s).")
    else:
        file_paths = ["sample_sales.csv"]
        st.info("Using default dataset: sample_sales.csv")

    st.markdown("---")
    st.header("2. Session Management")
    if st.button("Reset Session / Clear Graph State", type="secondary", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.success("Session reset. Fresh graph thread initialized.")
        st.rerun()

# Display persistent chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "chart" in msg and msg["chart"] is not None:
            st.plotly_chart(msg["chart"], use_container_width=True)

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# User Query Input and Autonomous Execution
if user_input := st.chat_input("Ask a question about your data..."):
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
        
        # Render outputs in Streamlit UI
        st.markdown("### Executive Summary")
        st.markdown(final_response)
        
        if executed_sql:
            st.markdown("### Executed SQL Query")
            st.code(executed_sql, language="sql")
            
        if query_result:
            st.markdown("### Query Results")
            st.markdown(query_result)
        
        # Execute and display Plotly chart safely
        fig_obj = None
        if chart_code:
            try:
                exec_globals = {"px": px, "pd": pd, "pio": pio}
                exec_locals = {}
                exec(chart_code, exec_globals, exec_locals)
                if "fig" in exec_locals:
                    fig_obj = exec_locals["fig"]
                    st.markdown("### Data Visualization")
                    st.plotly_chart(fig_obj, use_container_width=True)
            except Exception as e:
                st.caption(f"Chart execution failed: {e}")
        
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