# Agentic Data Science Engine

An interactive, multi-agent analytics workspace for exploring CSV and Parquet data with natural language.

Ask a question about your data and the engine coordinates a small LangGraph workflow that profiles the dataset, writes DuckDB SQL, executes it locally, creates a visualization when appropriate, and explains the result in plain language.

## What this project does

The application turns ordinary data analysis into a conversational workflow:

1. You upload a CSV or Parquet file, or use the included sample dataset.
2. The analyst agent interprets your question and generates SQL.
3. The SQL runner executes the query against DuckDB and retries when the query needs correction.
4. The visualizer creates a Plotly chart when the result is suitable for visualization.
5. The synthesizer returns an executive summary with the important findings.

The data processing stays local to the application. Only the language-model prompts and the context needed to answer a question are sent to the configured Groq model.

## Highlights

- Natural-language questions over CSV and Parquet files.
- Multi-agent orchestration with LangGraph.
- Local SQL execution through DuckDB.
- Automatic query repair with bounded retries.
- Interactive Plotly visualizations.
- Conversational history within a browser session.
- A clean Streamlit workspace with dataset preview, progress updates, and separate summary, data, and visualization tabs.

## How the workflow fits together

```text
User question
      |
      v
Supervisor --> Analyst --> SQL Runner --> Visualizer
      |            ^             |             |
      +------------+------ error +-------------+
      |
      v
Synthesizer --> Executive summary
```

## Project structure

| Path | Purpose |
| --- | --- |
| [`src/app.py`](./src/app.py) | Streamlit interface and result presentation |
| [`src/graph.py`](./src/graph.py) | LangGraph workflow and agent nodes |
| [`src/agent_state.py`](./src/agent_state.py) | Shared state passed between nodes |
| [`src/mcp_server.py`](./src/mcp_server.py) | Data-analysis tools exposed to the workflow |
| [`src/report_generator.py`](./src/report_generator.py) | Report and output helpers |
| [`tests/`](./tests/) | Automated tests |
| [`sample_sales.csv`](./sample_sales.csv) | Small dataset for trying the application |

## Requirements

- Python 3.11 or 3.12
- [`uv`](https://docs.astral.sh/uv/)
- A Groq API key

## Quick start

### 1. Install dependencies

From the project directory:

```powershell
uv sync
```

### 2. Configure the model

Create a local environment file from the template:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your key:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL_NAME=openai/gpt-oss-20b
```

Keep `.env` private and never commit it to source control.

### 3. Start the application

PowerShell:

```powershell
$env:PYTHONPATH="src"
uv run streamlit run src/app.py
```

macOS/Linux:

```bash
PYTHONPATH=src uv run streamlit run src/app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`.

## Example questions

After loading `sample_sales.csv`, try:

- “Which product category generated the most revenue?”
- “Show monthly revenue as a line chart.”
- “Compare average order value by region.”
- “What are the main trends and anomalies in this dataset?”

For reliable results, ask for a specific metric, grouping, filter, or time period. For example: “Calculate total revenue by region for 2025 and show it as a bar chart.”

## Testing

Run the test suite with:

```powershell
$env:PYTHONPATH="src"
uv run python -m unittest discover -s tests -v
```

## Configuration notes

- `GROQ_API_KEY` is required for agent reasoning.
- `GROQ_MODEL_NAME` controls which Groq chat model is used. Choose a model currently available to your account.
- Uploaded files are copied into a temporary workspace for the active session.
- Generated SQL is intended for local DuckDB execution and is not a replacement for production database access controls.

## Security and production considerations

This project is designed as a local development and analysis tool. Before exposing it to other users:

- Add authentication and authorization.
- Add upload size and file-type limits.
- Review generated code execution and isolate it in a restricted process.
- Add logging, rate limiting, and stronger secrets management.
- Avoid sending sensitive data to a third-party model provider unless your data policy allows it.

## License

This project is licensed under the MIT License.
