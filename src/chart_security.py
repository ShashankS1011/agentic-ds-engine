import ast
from typing import Any


def execute_chart_code(chart_code: str, *, px: Any, pd: Any) -> Any:
    """Execute the limited Plotly code format produced by the visualizer.

    Only pandas/Plotly Express imports and simple data/figure expressions are
    accepted. Builtins and all other imports are unavailable.
    """
    tree = ast.parse(chart_code, mode="exec")
    allowed_names = {"pd", "px", "fig", "df"}
    allowed_nodes = (
        ast.Module, ast.Import, ast.ImportFrom, ast.alias, ast.Assign,
        ast.Expr, ast.Call, ast.Attribute, ast.Name, ast.Load, ast.Store,
        ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.keyword,
        ast.Subscript, ast.Index, ast.Slice, ast.BinOp, ast.Add,
    )

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Unsupported chart-code construct: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            raise ValueError(f"Unsupported chart-code name: {node.id}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if (alias.name, alias.asname) not in {
                    ("pandas", "pd"),
                    ("plotly.express", "px"),
                }:
                    raise ValueError("Only pandas and Plotly Express imports are allowed")
        if isinstance(node, ast.ImportFrom):
            raise ValueError("From-import statements are not allowed")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError("Dunder attributes are not allowed")

    # The approved modules are supplied by the caller, so remove their import
    # statements before execution and keep builtins unavailable.
    tree.body = [node for node in tree.body if not isinstance(node, ast.Import)]
    exec_globals = {"__builtins__": {}, "px": px, "pd": pd}
    exec_locals: dict[str, Any] = {}
    exec(compile(tree, "<chart_code>", "exec"), exec_globals, exec_locals)
    return exec_locals.get("fig")
