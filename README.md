# Agentic Data Science Engine

Agentic Data Science Engine is a local Streamlit app for asking natural-language questions about CSV and Parquet files. It uses LangGraph to coordinate a small analysis workflow:

1. Profile the uploaded datasets.
2. Generate DuckDB SQL from the user's question.
3. Execute the query locally and retry failed SQL up to three times.
4. Create a Plotly chart when the result is suitable for visualization.
5. Return a concise executive summary and an optional downloadable HTML report.

The datasets and SQL execution stay local. The question and query context are sent to the configured Groq model for reasoning, so do not use sensitive data unless your data policy permits it.

## Features

- Natural-language analysis of CSV and Parquet files
- Multiple-file uploads for related datasets
- DuckDB execution without a separate database server
- Bounded SQL self-correction
- Interactive Plotly visualizations
- Session-based conversation history
- SQL, result, chart, and summary views
- Downloadable HTML reports
- Automated tests for data access, report escaping, and chart-code restrictions

## Requirements

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/)
- A Groq API key

## Quick start

Install dependencies from the project directory:

```powershell
uv sync
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Then set your credentials in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=openai/gpt-oss-20b
```

Start the Streamlit app:

```powershell
$env:PYTHONPATH="src"
uv run streamlit run src/app.py
```

Open the local URL shown by Streamlit, usually `http://localhost:8501`.

The app uses [`sample_sales.csv`](./sample_sales.csv) when no files are uploaded. You can also upload one or more `.csv` or `.parquet` files from the sidebar.

## Example questions

- Which product category generated the most revenue?
- Show monthly revenue as a line chart.
- Compare average order value by region.
- What are the main trends and anomalies in this dataset?
- Calculate total revenue by region for 2025 and show it as a bar chart.

Specific questions that name a metric, grouping, filter, or time period generally produce the most useful results.

## Project structure

| Path | Purpose |
| --- | --- |
| [`src/app.py`](./src/app.py) | Streamlit interface, result display, and report download |
| [`src/graph.py`](./src/graph.py) | LangGraph workflow and agent nodes |
| [`src/agent_state.py`](./src/agent_state.py) | Shared workflow state |
| [`src/mcp_server.py`](./src/mcp_server.py) | Dataset profiling and DuckDB execution |
| [`src/chart_security.py`](./src/chart_security.py) | Restricted execution for generated chart code |
| [`src/report_generator.py`](./src/report_generator.py) | HTML report generation |
| [`tests/`](./tests/) | Automated tests |

The workflow is:

```text
Question
   |
Supervisor -> Analyst -> SQL runner -> Visualizer -> Synthesizer
      ^          |             |
      +----------+-------------+  (retry failed SQL up to 3 times)
```

## Testing

Run the test suite:

```powershell
$env:PYTHONPATH="src"
uv run python -m unittest discover -s tests -v
```

Check that all Python files compile:

```powershell
$env:PYTHONPATH="src"
uv run python -m compileall -q src tests
```

The `agentic-ds-engine` command runs a sample command-line analysis. It requires the same `.env` configuration as the Streamlit app:

```powershell
$env:PYTHONPATH="src"
uv run agentic-ds-engine
```

## Configuration and data handling

- `GROQ_API_KEY` is required for agent reasoning.
- `GROQ_MODEL_NAME` selects the Groq chat model.
- Uploaded files are copied into a temporary directory for the current browser session.
- Generated SQL reads CSV and Parquet files directly with DuckDB reader functions.
- Local `.env` files, databases, caches, coverage output, and Streamlit secrets are ignored by Git.

## Security notes

This application is intended for local development and trusted users. Before deploying it for other users:

- Add authentication and authorization.
- Enforce upload size and file-type limits.
- Use stronger secrets management.
- Add logging and rate limiting.
- Review whether sending schema and query context to a hosted model is acceptable.

Generated chart code is parsed and restricted to a small pandas/Plotly Express subset before execution. This reduces risk, but it is not a replacement for process isolation in an untrusted multi-user deployment.

## License

This project is licensed under the MIT License.
