from typing import TypedDict, List, Annotated
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    dataset_paths: List[str]
    sql_query: str
    query_result: str
    chart_code: str
    chart_evaluated: bool
    is_approved: bool
    status: str
    retry_count: int
    next_node: str  # Added to track active routing target