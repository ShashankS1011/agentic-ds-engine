from mcp_server import profile_dataset, execute_sql

print("--- Testing profile_dataset ---")
profile = profile_dataset("sample_sales.csv")
print(profile)

print("\n--- Testing execute_sql ---")
# Create a DuckDB table from our CSV and query it
import duckdb
conn = duckdb.connect("warehouse.db")
conn.execute("CREATE TABLE IF NOT EXISTS sales AS SELECT * FROM read_csv_auto('sample_sales.csv')")
conn.close()

sql_result = execute_sql("SELECT product, SUM(price * sales) AS total_revenue FROM sales GROUP BY product", "warehouse.db")
print(sql_result)