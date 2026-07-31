import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.llms import Ollama  # Or your LLM wrapper of choice


ANALYST_SYSTEM_PROMPT = """You are an expert SQL Data Analyst working with DuckDB.
Your task is to translate user natural language questions into highly accurate, performant SQL queries.

CRITICAL DUCKDB FILE-QUERYING RULES:
1. ALWAYS use `read_csv_auto('path/to/file.csv')` or `read_csv_auto('filename.csv')` in your `FROM` and `JOIN` clauses.
2. NEVER use bare table names like `FROM customers` or `FROM orders`. Tables do NOT exist in the database catalog unless loaded with `read_csv_auto()`.
   - BAD: `FROM customers c JOIN orders o ON ...`
   - GOOD: `FROM read_csv_auto('customers.csv') c JOIN read_csv_auto('orders.csv') o ON ...`
3. Float Division: Use `100.0` (with a decimal point) instead of `100` when calculating percentages to prevent integer division truncation to 0.
4. Conditional Aggregation: When filtering metrics (e.g., revenue from 'completed' status only), use `SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END)`.
5. Group By: Ensure all non-aggregated columns in the SELECT clause are present in the `GROUP BY` clause.

AVAILABLE DATASETS:
{dataset_info}

Return ONLY the raw SQL query string inside your text response or fenced inside ```sql ... ``` blocks. Do not include conversational preambles.
"""


def analyst_node(state: dict) -> dict:
    """
    Analyst Node: Receives user prompt and available dataset paths, 
    then uses Qwen 2.5 Coder to generate an accurate DuckDB SQL query.
    """
    messages = state.get("messages", [])
    dataset_paths = state.get("dataset_paths", [])

    # Format the dataset list for the prompt
    if dataset_paths:
        formatted_paths = "\n".join([f"- {path}" for path in dataset_paths])
        dataset_info = f"The following files are available to query directly:\n{formatted_paths}"
    else:
        dataset_info = "No specific files provided. Use `read_csv_auto('sample_sales.csv')` by default."

    # Construct System Message with exact DuckDB instructions
    system_message = SystemMessage(content=ANALYST_SYSTEM_PROMPT.format(dataset_info=dataset_info))
    
    # Initialize your LLM (Adjust model name / base_url as configured in your setup)
    llm = Ollama(model="qwen2.5-coder", temperature=0)
    
    # Combine system instructions with full conversation context
    prompt_messages = [system_message] + messages
    
    # Invoke model
    response = llm.invoke(prompt_messages)
    
    # Clean up response to extract raw SQL if wrapped in markdown code blocks
    raw_content = response.content if hasattr(response, "content") else str(response)
    clean_sql = raw_content.replace("```sql", "").replace("```", "").strip()

    return {
        "sql_query": clean_sql,
        "status": "sql_generated"
    }