<<<<<<< HEAD
# Agentic Data Science Engine

An autonomous multi-agent analytics platform built with LangGraph, DuckDB, Groq, and Streamlit.

The engine converts natural language user queries into executable DuckDB SQL, runs analysis against local CSV and Parquet datasets, generates dynamic interactive visualizations, and synthesizes natural-language executive summaries. It features an automated self-healing execution loop to recover from runtime database errors without user intervention.

---

## Architecture Overview

The core workflow is governed by a LangGraph state graph using a supervisor-worker pattern:

- **Supervisor Node:** Directs state transitions and routes execution between worker agents based on current state attributes and retry counts.
- **Analyst Node:** Inspects dataset profiles and generates dialect-accurate DuckDB SQL queries. If an execution error occurs, it analyzes the database exception trace to rewrite the SQL query.
- **SQL Runner Node:** Executes generated SQL queries against the local DuckDB engine and handles error trapping.
- **Visualizer Node:** Evaluates tabular query output and synthesizes executable Python Plotly code for visual display.
- **Synthesizer Node:** Interprets raw query results and generates structured executive summaries and actionable business insights.

---

## Core Features

- **Multi-Agent Orchestration:** Powered by LangGraph state graphs with strict typing and persistent thread checkpointing.
- **Self-Healing SQL Retry Loop:** Automatically intercepts DuckDB syntax or schema errors, routes exception traces back to the Analyst node, and attempts up to 3 automatic correction cycles.
- **In-Memory SQL Performance:** Direct SQL queries over CSV and Parquet files using DuckDB auto-schema discovery (`read_csv_auto` and `read_parquet`).
- **Dynamic Visualization:** Generates customized Plotly Express charts dynamically tailored to the schema of the returned dataset.
- **State Persistence:** Maintains query, code, visual, and message history per session using Streamlit state management.

---

## Project Structure

```text
agentic-ds-engine/
├── src/
│   ├── app.py             # Streamlit user interface and event streaming
│   ├── graph.py           # LangGraph orchestration logic and node definitions
│   ├── agent_state.py     # TypedDict state schema definitions
│   ├── mcp_server.py      # DuckDB execution module and schema profiler
│   ├── report_generator.py# Export and reporting utilities
│   └── nodes/             # Extensible pipeline components
├── sample_sales.csv       # Sample dataset
├── customers.csv          # Sample dataset
├── orders.csv             # Sample dataset
├── pyproject.toml         # Dependency and environment configuration
├── .env.example           # Environment template
└── README.md              # Project documentation
```

---

## Prerequisites

- Python 3.11 or higher
- `uv` package manager
- Groq API Key

---

## Quickstart Guide

### 1. Repository Setup

Clone the repository to your local machine:

```bash
git clone [https://github.com/YOUR_USERNAME/agentic-ds-engine.git](https://github.com/YOUR_USERNAME/agentic-ds-engine.git)
cd agentic-ds-engine
```

### 2. Environment Configuration

Copy the sample environment file and add your credentials:

```bash
cp .env.example .env
```

Open `.env` in your editor and set your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Install Dependencies

Install the project virtual environment and required libraries using `uv`:

```bash
uv sync
```

### 4. Run the Application

Execute the application using the commands appropriate for your operating system:

- **Linux / macOS:**

```bash
PYTHONPATH=src uv run streamlit run src/app.py
```

- **Windows (PowerShell):**

```powershell
$env:PYTHONPATH="src"; uv run streamlit run src/app.py
```

---

## Technology Stack

- **Orchestration:** LangGraph / LangChain
- **Language Model:** Groq (`llama-3.3-70b-versatile`)
- **Query Engine:** DuckDB
- **User Interface:** Streamlit
- **Visualization:** Plotly Express
- **Package Management:** `uv`

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
=======
# agentic-ds-engine
>>>>>>> 92b1dd1506b556c41a6c73d26bb291286dae13d3
