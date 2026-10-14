import sys
import unittest
from unittest import mock
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from mcp_server import execute_sql, profile_dataset
from report_generator import generate_html_report
from chart_security import execute_chart_code
from security import (
    authentication_enabled,
    get_positive_int,
    password_is_valid,
    validate_read_only_sql,
    validate_upload,
    username_is_valid,
)


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

    def test_execute_sql_rejects_write_queries(self):
        result = execute_sql("DROP TABLE sales")

        self.assertIn("Only SELECT and WITH queries are allowed", result)

    def test_read_only_sql_validation_rejects_multiple_statements(self):
        self.assertEqual(
            "Only one SQL statement is allowed.",
            validate_read_only_sql("SELECT 1; SELECT 2"),
        )
        self.assertIsNone(validate_read_only_sql("WITH values AS (SELECT 1) SELECT * FROM values"))

    def test_upload_validation_enforces_type_and_size(self):
        self.assertIsNone(validate_upload("sales.csv", 1024, 1))
        self.assertIn("Only CSV", validate_upload("sales.xlsx", 1024, 1))
        self.assertIn("upload limit", validate_upload("sales.csv", 2 * 1024 * 1024, 1))

    def test_invalid_integer_setting_uses_safe_default(self):
        with mock.patch.dict("os.environ", {"MAX_UPLOAD_FILES": "not-a-number"}):
            self.assertEqual(10, get_positive_int("MAX_UPLOAD_FILES", 10))

    def test_configured_authentication_checks_credentials(self):
        with mock.patch.dict(
            "os.environ", {"APP_USERNAME": "analyst", "APP_PASSWORD": "secret"}
        ):
            self.assertTrue(authentication_enabled())
            self.assertTrue(username_is_valid("analyst"))
            self.assertFalse(username_is_valid("other"))
            self.assertTrue(password_is_valid("secret"))
            self.assertFalse(password_is_valid("wrong"))

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
        fig = execute_chart_code(
            "import pandas as pd\nimport plotly.express as px\n"
            "df = pd.DataFrame({'category': ['A'], 'value': [1]})\n"
            "fig = px.bar(df, x='category', y='value')",
        )

        self.assertIsNotNone(fig)

    def test_chart_code_rejects_unsafe_names(self):
        with self.assertRaises(ValueError):
            execute_chart_code("__import__('os').system('whoami')")
