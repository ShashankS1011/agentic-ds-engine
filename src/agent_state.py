import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    dataset_paths: list[str]
    sql_query: str
    query_result: str
    chart_code: str
    chart_evaluated: bool
    is_approved: bool
    status: str
    retry_count: int
    next_node: str
