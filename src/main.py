from langchain_core.messages import HumanMessage

def main() -> None:
    """Run a sample analysis from the command line."""
    from graph import app

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
    config = {"configurable": {"thread_id": "cli-sample"}}
    for output in app.stream(initial_state, config=config):
        for node_name, state_update in output.items():
            print(f"=== Node Executed: {node_name} ===")
            if "messages" in state_update and state_update["messages"]:
                print(f"Message: {state_update['messages'][-1].content}\n")
            elif "next_node" in state_update:
                print(f"Supervisor Decision -> Next: {state_update['next_node']}\n")


if __name__ == "__main__":
    main()
