from langchain_core.messages import HumanMessage
from graph import app

if __name__ == "__main__":
    initial_state = {
        "messages": [HumanMessage(content="Which product generated the highest revenue?")],
        "dataset_paths": ["sample_sales.csv"],
        "sql_query": "",
        "query_result": "",
        "chart_code": "",
        "chart_evaluated": False,
        "is_approved": True,
        "retry_count": 0,
        "next_node": "",
        "status": "started"
    }

    print("--- Starting Agentic Workflow ---\n")
    
    # Run graph execution loop
    for output in app.stream(initial_state):
        for node_name, state_update in output.items():
            print(f"=== Node Executed: {node_name} ===")
            if "messages" in state_update and state_update["messages"]:
                print(f"Message: {state_update['messages'][-1].content}\n")
            elif "next_node" in state_update:
                print(f"Supervisor Decision -> Next: {state_update['next_node']}\n")