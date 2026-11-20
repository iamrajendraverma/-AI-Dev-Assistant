"""Local mock REST APIs for Jira, GitHub, Slack, and external services."""
from pathlib import Path
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]

def load_json(path):
    return json.loads((ROOT / path).read_text())

JIRA = {x["key"]: x for x in load_json("mock_data/jira_issues.json")["issues"]}
REPOS = {(x["owner"], x["name"]): x for x in load_json("mock_data/github_repositories.json")["repositories"]}
EXTERNAL = load_json("mock_data/external_services.json")
PULLS = {}
BRANCHES = {}
SLACK_MESSAGES = []

app = FastAPI(title="Mock Dev Platform APIs", version="1.0.0")

class CreateIssue(BaseModel):
    summary: str
    description: str = ""
    priority: str = "Medium"
    repository: Optional[str] = None
    github_owner: Optional[str] = None
    acceptance_criteria: list[str] = Field(default_factory=list)

class UpdateIssue(BaseModel):
    status: Optional[str] = None
    fields: dict = Field(default_factory=dict)

class Comment(BaseModel):
    comment: str

class CreateBranch(BaseModel):
    branch_name: str
    from_branch: str = "main"

class CreatePull(BaseModel):
    title: str
    body: str = ""
    head: str
    base: str = "main"
    idempotency_key: str

class SlackMessage(BaseModel):
    channel: str
    text: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-dev-platform"}

@app.get("/jira/issues")
def list_issues():
    return {"issues": list(JIRA.values())}

@app.get("/jira/issues/{issue_key}")
def get_issue(issue_key: str):
    if issue_key not in JIRA:
        raise HTTPException(404, detail=f"Jira issue {issue_key} not found")
    return JIRA[issue_key]

@app.post("/jira/issues", status_code=201)
def create_issue(payload: CreateIssue):
    number = 100 + len(JIRA) + 1
    key = f"PROJ-{number}"
    issue = {
        "key": key, "summary": payload.summary, "description": payload.description,
        "status": "To Do", "priority": payload.priority, "assignee": "Unassigned",
        "reporter": "Machine Test", "repository": payload.repository,
        "github_owner": payload.github_owner,
        "acceptance_criteria": payload.acceptance_criteria, "labels": [], "comments": []
    }
    JIRA[key] = issue
    return issue

@app.patch("/jira/issues/{issue_key}")
def update_issue(issue_key: str, payload: UpdateIssue):
    if issue_key not in JIRA:
        raise HTTPException(404, detail="Issue not found")
    allowed = {"To Do", "In Progress", "Done", "Backlog", "Blocked"}
    if payload.status is not None:
        if payload.status not in allowed:
            raise HTTPException(422, detail=f"Invalid status. Allowed: {sorted(allowed)}")
        JIRA[issue_key]["status"] = payload.status
    JIRA[issue_key].update(payload.fields)
    return JIRA[issue_key]

@app.post("/jira/issues/{issue_key}/comments", status_code=201)
def add_comment(issue_key: str, payload: Comment):
    if issue_key not in JIRA:
        raise HTTPException(404, detail="Issue not found")
    item = {"body": payload.comment, "author": "mock-agent"}
    JIRA[issue_key]["comments"].append(item)
    return item

@app.get("/github/repos/{owner}/{repo}")
def get_repo(owner: str, repo: str):
    item = REPOS.get((owner, repo))
    if not item:
        raise HTTPException(404, detail="Repository not found")
    return item

@app.get("/github/repos/{owner}/{repo}/files")
def list_files(owner: str, repo: str):
    item = REPOS.get((owner, repo))
    if not item:
        raise HTTPException(404, detail="Repository not found")
    return {"owner": owner, "repo": repo, "files": item["files"]}

@app.get("/github/repos/{owner}/{repo}/file")
def read_file(owner: str, repo: str, path: str = Query(...)):
    item = REPOS.get((owner, repo))
    if not item:
        raise HTTPException(404, detail="Repository not found")
    if path not in item["files"]:
        raise HTTPException(404, detail="File not found")
    file_path = ROOT / "mock_github" / repo / path
    if not file_path.exists():
        raise HTTPException(404, detail="Mock file content not found")
    return {"path": path, "content": file_path.read_text()}

@app.post("/github/repos/{owner}/{repo}/branches", status_code=201)
def create_branch(owner: str, repo: str, payload: CreateBranch):
    if (owner, repo) not in REPOS:
        raise HTTPException(404, detail="Repository not found")
    if payload.from_branch != REPOS[(owner, repo)]["default_branch"]:
        raise HTTPException(422, detail="Base branch does not exist")
    branches = BRANCHES.setdefault((owner, repo), set())
    if payload.branch_name in branches:
        return {"created": False, "branch": payload.branch_name, "message": "Branch already exists"}
    branches.add(payload.branch_name)
    return {"created": True, "branch": payload.branch_name, "from_branch": payload.from_branch}

@app.get("/github/repos/{owner}/{repo}/pulls")
def list_pulls(owner: str, repo: str):
    if (owner, repo) not in REPOS:
        raise HTTPException(404, detail="Repository not found")
    return {"pull_requests": PULLS.get((owner, repo), [])}

@app.post("/github/repos/{owner}/{repo}/pulls", status_code=201)
def create_pull(owner: str, repo: str, payload: CreatePull):
    if (owner, repo) not in REPOS:
        raise HTTPException(404, detail="Repository not found")
    existing = PULLS.setdefault((owner, repo), [])
    for pr in existing:
        if pr["idempotency_key"] == payload.idempotency_key:
            return {**pr, "created": False, "message": "Existing PR returned"}
    if payload.head not in BRANCHES.get((owner, repo), set()):
        raise HTTPException(422, detail="Head branch must exist before PR creation")
    pr = {
        "number": len(existing) + 1,
        "title": payload.title, "body": payload.body, "head": payload.head,
        "base": payload.base, "state": "open",
        "html_url": f"https://github.com/{owner}/{repo}/pull/{len(existing)+1}",
        "idempotency_key": payload.idempotency_key
    }
    existing.append(pr)
    return {**pr, "created": True}

@app.post("/slack/messages", status_code=201)
def send_slack(payload: SlackMessage):
    allowed = EXTERNAL["slack_channels"]
    if payload.channel not in allowed:
        raise HTTPException(422, detail=f"Unknown channel. Allowed: {allowed}")
    message = {"channel": payload.channel, "text": payload.text, "ts": str(len(SLACK_MESSAGES)+1)}
    SLACK_MESSAGES.append(message)
    return {"ok": True, "message": message}

@app.get("/external/quality/{owner}/{repo}")
def quality_scan(owner: str, repo: str):
    if (owner, repo) not in REPOS:
        raise HTTPException(404, detail="Repository not found")
    return EXTERNAL["quality_scans"][repo]

@app.get("/external/deployments/{service}")
def deployment_status(service: str):
    item = EXTERNAL["deployments"].get(service)
    if not item:
        raise HTTPException(404, detail="Deployment not found")
    return item
