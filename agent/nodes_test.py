
from agent.nodes import fetch_jira_issue,fetch_github_repository,retrieve_source_files,generate_implementation_plan,human_approval,implement_code,write_generated_files
from agent.state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import json



def run_human_approval(state: dict) -> dict:
    # interrupt() needs a graph runtime, so run the node inside a tiny graph.
    builder = StateGraph(AgentState)
    builder.add_node("human_approval", human_approval)
    builder.add_edge(START, "human_approval")
    builder.add_edge("human_approval", END)
    graph = builder.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "nodes-test"}}

    graph.invoke(state, config)  # pauses at interrupt()
    # Auto-approve for this test run.
    return graph.invoke(Command(resume={"approved": True}), config)


def main():

    initial_state = {
        "jira_id": "PROJ-101"
    }

    jira_result = fetch_jira_issue(initial_state)
    initial_state.update(jira_result)

    github_result = fetch_github_repository(initial_state)
    initial_state.update(github_result)
    resource_file  =  retrieve_source_files(initial_state)
    initial_state.update(resource_file)
    plan_to_implement  = generate_implementation_plan(initial_state)
    initial_state.update(plan_to_implement)

    human_review  = run_human_approval(initial_state)
    initial_state.update(human_review)
    implemented_code  =implement_code(initial_state)
    initial_state.update(implemented_code)
    generate_code = write_generated_files(initial_state)
    initial_state.update(generate_code)
    print(f"File Output{json.dumps(initial_state,indent=5)}")

    

    



if __name__ == "__main__":
    main()
