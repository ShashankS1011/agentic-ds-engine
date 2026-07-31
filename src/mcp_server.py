import duckdb
import pandas as pd
from typing import List

def profile_dataset(file_paths: List[str]) -> str:
    """Profiles multiple CSV or Parquet files using DuckDB to extract table names, column names, and data types."""
    if not file_paths:
        return "No datasets provided."
        
    profiles = []
    con = duckdb.connect(database=":memory:")
    
    for file_path in file_paths:
        try:
            table_alias = file_path.split("/")[-1].split("\\")[-1].replace(".csv", "").replace(".parquet", "")
            if file_path.endswith(".csv"):
                df = con.execute(f"SELECT * FROM read_csv_auto('{file_path}') LIMIT 5").df()
            elif file_path.endswith(".parquet"):
                df = con.execute(f"SELECT * FROM read_parquet('{file_path}') LIMIT 5").df()
            else:
                continue
            
            columns_info = [f"  - {col} ({df[col].dtype})" for col in df.columns]
            cols_str = "\n".join(columns_info)
            profiles.append(f"Table Name / File: '{file_path}' (Alias: {table_alias})\nColumns:\n{cols_str}")
        except Exception as e:
            profiles.append(f"Error profiling '{file_path}': {str(e)}")
            
    con.close()
    return "\n\n".join(profiles)

def execute_sql(sql_query: str, db_path: str = "warehouse.db") -> str:
    """Executes a DuckDB SQL query and returns markdown table output or error message."""
    if not sql_query or sql_query.strip() == "":
        return "Error: No SQL query was provided to execute."
    
    try:
        con = duckdb.connect(database=db_path)
        result_df = con.execute(sql_query).df()
        con.close()
        
        if result_df.empty:
            return "Query executed successfully. No rows returned."
        
        return result_df.to_markdown(index=False)
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"