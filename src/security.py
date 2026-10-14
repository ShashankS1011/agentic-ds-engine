import hmac
import os
import re
from typing import Any


def get_setting(name: str, default: str | None = None) -> str | None:
    """Read a setting from environment variables or Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value

    try:
        import streamlit as st

        secret_value = st.secrets.get(name)
        return str(secret_value) if secret_value else default
    except Exception:
        return default


def get_positive_int(name: str, default: int) -> int:
    value = get_setting(name)
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def authentication_enabled() -> bool:
    return bool(get_setting("APP_PASSWORD"))


def username_is_valid(username: str) -> bool:
    expected = get_setting("APP_USERNAME")
    return not expected or hmac.compare_digest(username, expected)


def password_is_valid(password: str) -> bool:
    expected = get_setting("APP_PASSWORD")
    return bool(expected) and hmac.compare_digest(password, expected)


def validate_upload(filename: str, size_bytes: int, max_size_mb: int) -> str | None:
    """Return an error message when an upload is not allowed."""
    suffix = os.path.splitext(filename)[1].lower()
    if suffix not in {".csv", ".parquet"}:
        return "Only CSV and Parquet files are supported."
    if size_bytes > max_size_mb * 1024 * 1024:
        return f"File exceeds the {max_size_mb} MB upload limit."
    return None


_FORBIDDEN_SQL = re.compile(
    r"\b(ATTACH|ALTER|CALL|COPY|CREATE|DELETE|DETACH|DROP|EXPORT|IMPORT|"
    r"INSTALL|INSERT|LOAD|PRAGMA|RESET|SET|TRUNCATE|UPDATE|VACUUM)\b",
    re.IGNORECASE,
)


def validate_read_only_sql(sql_query: str) -> str | None:
    """Validate that a generated query is exactly one read-only statement."""
    without_comments = re.sub(r"--[^\r\n]*|/\*.*?\*/", " ", sql_query, flags=re.DOTALL)
    statements = [part.strip() for part in without_comments.split(";") if part.strip()]
    if len(statements) != 1:
        return "Only one SQL statement is allowed."

    statement = statements[0]
    if not re.match(r"^(SELECT|WITH)\b", statement, flags=re.IGNORECASE):
        return "Only SELECT and WITH queries are allowed."
    if _FORBIDDEN_SQL.search(statement):
        return "Write operations and administrative SQL are not allowed."
    return None


def render_login(st: Any) -> None:
    """Render the optional login gate and stop the Streamlit run if needed."""
    if not authentication_enabled() or st.session_state.get("authenticated"):
        return

    st.title("Sign in")
    st.caption("Authentication is enabled for this deployment.")
    username = st.text_input("Username", value=get_setting("APP_USERNAME", "") or "")
    password = st.text_input("Password", type="password")
    if st.button("Sign in", type="primary"):
        if username_is_valid(username) and password_is_valid(password):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Invalid username or password.")
    st.stop()
