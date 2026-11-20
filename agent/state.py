from typing import TypedDict, Any

class AgentState(TypedDict):
    jira_id :str
    jira_issue:dict[str,Any]
    repository:dict[str,Any]
    files:dict[str,Any]
    implementation_plan:str
    generated_files: dict[str, Any]
    approved:bool
    branch_name:str
    pr_url:str
    error:str