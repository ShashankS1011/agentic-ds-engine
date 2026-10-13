from pathlib import Path
from typing import Iterable

import duckdb


def _sql_string_literal(value: str) -> str:
    """Escape a filesystem path for use in a DuckDB string literal."""
    return "'" + value.replace("'", "''") + "'"


def _reader_for(path: Path) -> str | None:
    if path.suffix.lower() == ".csv":
        return "read_csv_auto"
    if path.suffix.lower() == ".parquet":
        return "read_parquet"
    return None


def profile_dataset(file_paths: Iterable[str] | str) -> str:
    """Profiles multiple CSV or Parquet files using DuckDB to extract table names, column names, and data types."""
    paths = [file_paths] if isinstance(file_paths, str) else list(file_paths)
    if not paths:
        return "No datasets provided."

    profiles = []
    with duckdb.connect(database=":memory:") as con:
        for file_path in paths:
            path = Path(file_path)
            reader = _reader_for(path)
            if reader is None:
                profiles.append(
                    f"Unsupported dataset '{file_path}'. Supported formats: CSV and Parquet."
                )
                continue

            try:
                table_alias = path.stem
                escaped_path = _sql_string_literal(str(path))
                df = con.execute(
                    f"SELECT * FROM {reader}({escaped_path}) LIMIT 5"
                ).df()
                columns_info = [f"  - {col} ({df[col].dtype})" for col in df.columns]
                cols_str = "\n".join(columns_info) or "  - No columns detected"
                profiles.append(
                    f"Table Name / File: '{file_path}' (Alias: {table_alias})\n"
                    f"Columns:\n{cols_str}"
                )
            except (duckdb.Error, OSError, ValueError) as exc:
                profiles.append(f"Error profiling '{file_path}': {exc}")

    return "\n\n".join(profiles)

def execute_sql(sql_query: str, db_path: str = "warehouse.db") -> str:
    """Executes a DuckDB SQL query and returns markdown table output or error message."""
    if not sql_query or sql_query.strip() == "":
        return "Error: No SQL query was provided to execute."
    
    try:
        with duckdb.connect(database=db_path, read_only=False) as con:
            result_df = con.execute(sql_query).df()

        if result_df.empty:
            return "Query executed successfully. No rows returned."

        return result_df.to_markdown(index=False)
    except (duckdb.Error, OSError, ValueError) as exc:
        return f"SQL Execution Error: {exc}"