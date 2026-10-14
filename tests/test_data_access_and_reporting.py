import sys
import unittest
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mcp_server import execute_sql, profile_dataset
from report_generator import generate_html_report
from chart_security import execute_chart_code


class DataAccessAndReportingTests(unittest.TestCase):
    def test_profile_dataset_accepts_single_path_and_reports_columns(self):
        dataset = Path(self.id().replace(".", "_") + "_sales.csv")
        try:
            dataset.write_text("product,amount\nWidget,12\n", encoding="utf-8")

            profile = profile_dataset(str(dataset))

            self.assertIn("Alias: " + dataset.stem, profile)
            self.assertIn("product", profile)
            self.assertIn("amount", profile)
        finally:
            dataset.unlink(missing_ok=True)

    def test_profile_dataset_escapes_paths_with_quotes(self):
        dataset = Path("owner's_sales.csv")
        try:
            dataset.write_text("product,amount\nWidget,12\n", encoding="utf-8")

            profile = profile_dataset([str(dataset)])

            self.assertIn("product", profile)
            self.assertNotIn("Error profiling", profile)
        finally:
            dataset.unlink(missing_ok=True)

    def test_execute_sql_closes_connection_and_returns_markdown(self):
        database = Path("test_warehouse.db")
        try:
            with duckdb.connect(str(database)) as connection:
                connection.execute("CREATE TABLE sales(product VARCHAR, amount INTEGER)")
                connection.execute("INSERT INTO sales VALUES ('Widget', 12)")

            result = execute_sql("SELECT * FROM sales", str(database))

            self.assertIn("| product", result)
            self.assertIn("Widget", result)
        finally:
            database.unlink(missing_ok=True)

    def test_report_escapes_user_controlled_text(self):
        report = generate_html_report(
            "<script>alert(1)</script>",
            "SELECT '<script>'",
            "<script>bad</script>",
            "<b>unsafe</b>",
        )

        self.assertNotIn("<script>alert(1)</script>", report)
        self.assertIn("&lt;script&gt;", report)

    def test_chart_code_allows_plotly_dataframe_creation(self):
        import pandas as pd
        import plotly.express as px

        fig = execute_chart_code(
            "import pandas as pd\nimport plotly.express as px\n"
            "df = pd.DataFrame({'category': ['A'], 'value': [1]})\n"
            "fig = px.bar(df, x='category', y='value')",
            px=px,
            pd=pd,
        )

        self.assertIsNotNone(fig)

    def test_chart_code_rejects_unsafe_names(self):
        import pandas as pd
        import plotly.express as px

        with self.assertRaises(ValueError):
            execute_chart_code("__import__('os').system('whoami')", px=px, pd=pd)
