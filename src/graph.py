import os
import re
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent_state import AgentState
from mcp_server import profile_dataset, execute_sql
from security import get_setting

load_dotenv()

groq_api_key = get_setting("GROQ_API_KEY")
groq_model = get_setting("GROQ_MODEL_NAME", "openai/gpt-oss-20b")

if not groq_api_key:
    raise RuntimeError("GROQ_API_KEY is required. Add it to your local .env file.")

llm = ChatGroq(model=groq_model, temperature=0, api_key=groq_api_key)

MAX_RETRIES = 3


def _contains_sql_error(result: str) -> bool:
    return "SQL Execution Error" in result or result.startswith("Error:")


def _extract_fenced_content(content: str, language: str) -> str:
    """Extract the first fenced block, or return the trimmed response."""
    pattern = rf"```(?:{re.escape(language)})?\s*(.*?)```"
    match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else content.strip()


class SupervisorDecision(BaseModel):
    next_node: Literal["analyst", "sql_runner", "visualizer", "synthesizer", "FINISH"] = Field(
        description="The next worker agent to route to, or FINISH if answer is complete."
    )
    reasoning: str = Field(description="Brief explanation for this routing decision.")


def supervisor_node(state: AgentState):
    structured_llm = llm.with_structured_output(SupervisorDecision)
    
    current_sql = state.get("sql_query", "").strip()
    current_result = state.get("query_result", "").strip()
    has_error = _contains_sql_error(current_result)
    chart_evaluated = state.get("chart_evaluated", False)
    retry_count = state.get("retry_count", 0)
    
    # 1. Handle SQL execution errors with retry cap
    if has_error:
        if retry_count < MAX_RETRIES:
            return {"next_node": "analyst"}
        else:
            return {"next_node": "synthesizer"}
            
    # 2. Force Analyst if no query exists
    if not current_sql:
        return {"next_node": "analyst"}
        
    # 3. Autonomous execution: run SQL Runner if query is generated but not executed
    if current_sql and not current_result:
        return {"next_node": "sql_runner"}
        
    # 4. Route to Visualizer once SQL has executed successfully
    if current_result and not chart_evaluated:
        return {"next_node": "visualizer"}

    # 5. Route to Synthesizer or FINISH
    prompt = [
        SystemMessage(content=(
            "You are the Data Science Lead supervisor orchestrating an autonomous data analysis pipeline.\n\n"
            f"CURRENT STATE:\n"
            f"- Prepared SQL Query: '{current_sql}'\n"
            f"- SQL Execution Result: '{current_result}'\n\n"
            "STRICT DECISION RULES:\n"
            "1. If a clear natural language summary has NOT been generated yet, route to 'synthesizer'.\n"
            "2. If the final summary is complete, route to 'FINISH'."
        ))
    ] + state["messages"]
    
    decision = structured_llm.invoke(prompt)
    return {"next_node": decision.next_node}


def analyst_node(state: AgentState):
    dataset_paths = state.get("dataset_paths", ["sample_sales.csv"])
    profile = profile_dataset(dataset_paths)
    last_result = state.get("query_result", "")
    retry_count = state.get("retry_count", 0)
    
    error_context = ""
    if _contains_sql_error(last_result):
        retry_count += 1
        error_context = (
            f"\n\nYOUR PREVIOUS QUERY FAILED (Attempt {retry_count}/{MAX_RETRIES}):\n"
            f"{last_result}\n"
            "Please analyze the DuckDB error message above, correct the SQL syntax or logic, and generate a fixed query."
        )
    
    prompt = [
        SystemMessage(content=(
            f"You are an expert SQL Data Analyst working with DuckDB. Here are the dataset profiles:\n{profile}\n\n"
            "CRITICAL DUCKDB RULES:\n"
            "1. ALWAYS query uploaded files directly using `read_csv_auto('filename.csv')` or `read_parquet('filename.parquet')` in `FROM` and `JOIN` clauses.\n"
            "2. NEVER reference bare table names like `FROM customers`. DuckDB tables do not exist in the catalog unless queried via `read_csv_auto()`.\n"
            "3. Use float division (e.g., `100.0` instead of `100`) when calculating percentages.\n"
            "4. For status-specific aggregation, use conditional aggregation: `SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END)`.\n"
            "5. Generate EXACTLY ONE valid executable SQL query wrapped inside code fences: ```sql ... ```"
            f"{error_context}"
        ))
    ] + state["messages"]
    
    response = llm.invoke(prompt)
    raw_content = response.content.strip()
    
    clean_sql = _extract_fenced_content(raw_content, "sql")
    
    return {
        "sql_query": clean_sql,
        "query_result": "",
        "chart_code": "",
        "chart_evaluated": False,
        "is_approved": True,
        "retry_count": retry_count,
        "messages": [HumanMessage(content=f"Proposed SQL Query (Attempt {retry_count + 1}):\n{clean_sql}")]
    }


def sql_runner_node(state: AgentState):
    sql_query = state.get("sql_query", "")
    result = execute_sql(sql_query)
    return {
        "query_result": result,
        "messages": [HumanMessage(content=f"SQL Query Result:\n{result}")]
    }


def visualizer_node(state: AgentState):
    query_result = state.get("query_result", "")
    
    # If the SQL failed and hit max retries, skip visualization
    if _contains_sql_error(query_result):
        return {"chart_code": "", "chart_evaluated": True}
        
    prompt = [
        SystemMessage(content=(
            "You are a Data Visualization Expert.\n"
            "Given the following Markdown table result, generate executable Python code using Plotly Express (`import plotly.express as px` and `import pandas as pd`).\n"
            "Create a clean DataFrame from the tabular data and store the Plotly figure object in a variable named `fig`.\n"
            "DO NOT include `fig.show()` in the code.\n"
            "If the data is a single scalar value or not suitable for plotting, respond with ONLY 'NONE'.\n"
            "Otherwise, respond strictly with executable Python code wrapped in ```python ... ``` fences.\n\n"
            f"Table Data:\n{query_result}"
        ))
    ] + state["messages"]
    
    response = llm.invoke(prompt)
    code = response.content.strip()
    
    clean_code = _extract_fenced_content(code, "python")
        
    return {
        "chart_code": clean_code if clean_code.upper() != "NONE" else "",
        "chart_evaluated": True,
        "messages": [HumanMessage(content="Visualizer evaluated dataset for charting.")]
    }


def synthesizer_node(state: AgentState):
    query_result = state.get("query_result", "")
    retry_count = state.get("retry_count", 0)
    
    if _contains_sql_error(query_result):
        summary_prompt = (
            f"The SQL query could not be executed successfully after {retry_count} auto-correction attempts.\n"
            f"Error details:\n{query_result}\n\n"
            "Explain the issue clearly to the user and suggest how they can rephrase their query or check their dataset schema."
        )
    else:
        summary_prompt = f"Provide a concise, professional executive summary based on the provided SQL execution result:\n{query_result}"
    
    prompt = [SystemMessage(content=summary_prompt)] + state["messages"]
    
    response = llm.invoke(prompt)
    return {
        "messages": [HumanMessage(content=f"Final Answer: {response.content}")]
    }


def router(state: AgentState):
    return state.get("next_node", "analyst")

# Build StateGraph
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("sql_runner", sql_runner_node)
workflow.add_node("visualizer", visualizer_node)
workflow.add_node("synthesizer", synthesizer_node)

workflow.add_edge(START, "supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "analyst": "analyst",
        "sql_runner": "sql_runner",
        "visualizer": "visualizer",
        "synthesizer": "synthesizer",
        "FINISH": END
    }
)

workflow.add_edge("analyst", "supervisor")
workflow.add_edge("sql_runner", "supervisor")
workflow.add_edge("visualizer", "supervisor")
workflow.add_edge("synthesizer", "supervisor")

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)
