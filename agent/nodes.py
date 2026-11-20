
from agent.state import AgentState
import requests
import os
from dotenv import load_dotenv
from agent.llm import llm
from langgraph.types import interrupt
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent


load_dotenv()

MOCK_API_BASE_URL = os.getenv("MOCK_API_BASE_URL")


def fetch_jira_issue(state: AgentState) -> dict:
    jira_id  = state["jira_id"]
    response = requests.get(
        f"{MOCK_API_BASE_URL}/jira/issues/{jira_id}"
    )

    response.raise_for_status()

    jira_issue = response.json()

    return {
        "jira_issue": jira_issue
    }

def fetch_github_repository(state: AgentState) -> dict:
    jira_issue = state["jira_issue"]
    github_owner  = jira_issue["github_owner"]
    repository  = jira_issue["repository"]
    response   = requests.get(f"{MOCK_API_BASE_URL}/github/repos/{github_owner}/{repository}",timeout=10)
    response.raise_for_status()
    data = response.json()
    
    return {
        "repository": data,    }

def retrieve_source_files(state: AgentState) -> dict:
    meta_deta = state["repository"]
    owner = meta_deta["owner"]
    name = meta_deta["name"]

    files = {}
    for file in meta_deta["files"]:
        response = requests.get(
            f"{MOCK_API_BASE_URL}/github/repos/{owner}/{name}/file",
            params={"path": file},
            timeout=10,
        )
        response.raise_for_status()
        files[file] = response.json()["content"]

    return {"files": files}

def generate_implementation_plan(state: AgentState) -> dict:
    # Analyze Jira acceptance criteria and source files

    jira_data  = state["jira_issue"]
    summary  = jira_data["summary"]
    description  = jira_data["description"]
    acceptance_criteria = jira_data["acceptance_criteria"]
    source_files  = state["files"]

    prompt = f"""
You are a senior software engineer.

Analyze the Jira requirement and existing repository code.

Jira Summary:
{summary}

Jira Description:
{description}

Acceptance Criteria:
{acceptance_criteria}

Existing Source Code:
{source_files}

Tasks:
1. Analyze each acceptance criterion.
2. Identify files that need modification.
3. Explain the required code changes.
4. Identify required unit tests.
5. Identify potential risks.

Return a structured implementation plan.

Important rules:

1. Inspect the existing source code before proposing changes.
2. Do not propose modifying a file if its existing implementation
   already satisfies the acceptance criterion.
3. Reuse existing functions wherever possible.
4. Separate API validation from business logic validation.
5. For every acceptance criterion, classify it as:
   - Already implemented
   - Partially implemented
   - Not implemented
6. Do not introduce requirements that are not present in the Jira ticket.
7. Do not propose production deployment unless explicitly requested.
8. Identify which tests should be API tests and which should
   be unit tests.
"""

   
    response = llm.invoke(prompt)

    plan = response.content

    
   
    return {
        "implementation_plan": plan
    }

def human_approval(state: AgentState) -> dict:

    decision = interrupt({
        "message": "Please review the implementation plan.",
        "implementation_plan": state["implementation_plan"],
        "question": "Do you approve this implementation plan?"
    })

    return {
        "approved": decision["approved"]
    }

from agent.llm import llm
from agent.state import AgentState
import json


def implement_code(state: AgentState) -> dict:

    if not state["approved"]:
        raise ValueError("Implementation plan was not approved")

    prompt = f"""
    You are a senior Python developer.

    Jira requirements:
    {state["jira_issue"]}

    Acceptance criteria:
    {state["jira_issue"]["acceptance_criteria"]}

    Approved implementation plan:
    {state["implementation_plan"]}

    Existing source files:
    {state["files"]}

    Implement the required changes.

    Return ONLY valid JSON in this format:
    {{
        "files": {{
            "app.py": "complete updated source code",
            "tests/test_lab.py": "complete updated test code"
        }},
        "summary": "brief implementation summary"
    }}

    Rules:
    1. Return complete file contents, not partial snippets.
    2. Do not modify unrelated files.
    3. Follow existing project patterns.
    4. Satisfy every acceptance criterion.
    """

    # format="json" makes Ollama return raw JSON instead of prose or code fences.
    response = llm.bind(format="json").invoke(prompt)

    implementation = json.loads(response.content)

    return {
        "files": implementation["files"]
    }
def write_generated_files(state: AgentState) -> dict:

    if not state["approved"]:
        raise ValueError("Implementation was not approved")

    generated_files = state["files"]

    for file_name, content in generated_files.items():

        file_path = PROJECT_ROOT / "working_repo" / file_name

        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding="utf-8")

    return {
        "error": ""
    }
    