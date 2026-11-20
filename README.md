# Jira + GitHub + External Tools — 2-Hour Machine Test

**Level:** Senior AI / Agentic AI Engineer  
**Time limit:** 2 hours  
**Integration requirement:** Direct REST API **and** MCP  
**Rule:** This package contains mock services, mock data, starter repository files, requirements, and evaluator tests. It intentionally does **not** contain the LangGraph agent or orchestration solution.

## Your assignment

Build an AI-powered software-development assistant that accepts a natural-language request, retrieves a Jira issue, inspects the related GitHub repository, proposes a safe implementation plan, waits for human approval, creates a branch and pull request, and updates Jira. It must support both:
1. Direct REST API tools.
2. MCP tools exposed by the supplied MCP server.

You may implement one shared business layer and two adapters, or another clean design. Do not bypass approval for write operations.

## Scenario

User request:

> Inspect PROJ-101, identify the correct code changes in the healthcare-backend repository, prepare an implementation plan, and after approval create a branch and pull request. Then add the PR URL to Jira and move the issue to In Progress.

The mock Jira issue is linked to `acme-health/healthcare-backend`.

## Package layout

```text
.
├── README.md
├── requirements.txt
├── .env.example
├── mock_data/
│   ├── jira_issues.json
│   ├── github_repositories.json
│   └── external_services.json
├── mock_github/
│   ├── healthcare-backend/
│   │   ├── app.py
│   │   ├── patient_service.py
│   │   ├── lab_service.py
│   │   ├── medication_service.py
│   │   └── tests/test_lab.py
│   └── insurance-service/
│       ├── app.py
│       ├── claim_service.py
│       └── tests/test_claim.py
├── mock_services/
│   └── api.py
├── mcp_server/
│   └── server.py
└── evaluation/
    └── test_mock_api.py
```

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn mock_services.api:app --reload --port 8000
```

The REST mock server is available at `http://127.0.0.1:8000`. Open
`http://127.0.0.1:8000/docs` for Swagger UI and
`http://127.0.0.1:8000/health` for a health check.

### MCP server

In a second terminal:

```bash
python -m mcp_server.server
```

The MCP server uses stdio transport and exposes Jira, GitHub, and Slack-like tools.
Configure it as an MCP server in your MCP client. Example local config:

```json
{
  "mcpServers": {
    "mock-dev-platform": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/ABSOLUTE/PATH/TO/jira_github_machine_test"
    }
  }
}
```

The MCP server is an adapter over the same mock data and behavior as the REST API.
It is provided so you can test tool discovery and invocation. Your task is to connect
your agent to it; do not assume MCP tools are automatically available to LangGraph.

## REST API contract

All endpoints are prefixed by the local server root.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/jira/issues/{issue_key}` | Fetch issue |
| GET | `/jira/issues` | List issues |
| POST | `/jira/issues` | Create issue |
| PATCH | `/jira/issues/{issue_key}` | Update status / fields |
| POST | `/jira/issues/{issue_key}/comments` | Add comment |
| GET | `/github/repos/{owner}/{repo}` | Repository metadata |
| GET | `/github/repos/{owner}/{repo}/files` | List tracked files |
| GET | `/github/repos/{owner}/{repo}/file` | Read file (`path` query parameter) |
| POST | `/github/repos/{owner}/{repo}/branches` | Create branch |
| POST | `/github/repos/{owner}/{repo}/pulls` | Create pull request |
| GET | `/github/repos/{owner}/{repo}/pulls` | List pull requests |
| POST | `/slack/messages` | Send mock notification |
| GET | `/external/quality/{owner}/{repo}` | Mock quality scan |
| GET | `/external/deployments/{service}` | Mock deployment status |

Writes are simulated in memory for the lifetime of the API process. Restarting the server resets state from JSON files.

### Example requests

```bash
curl http://127.0.0.1:8000/jira/issues/PROJ-101
curl http://127.0.0.1:8000/github/repos/acme-health/healthcare-backend/files
curl "http://127.0.0.1:8000/github/repos/acme-health/healthcare-backend/file?path=lab_service.py"
```

Create a branch:

```bash
curl -X POST http://127.0.0.1:8000/github/repos/acme-health/healthcare-backend/branches \
  -H 'Content-Type: application/json' \
  -d '{"branch_name":"feature/PROJ-101-hba1c-report","from_branch":"main"}'
```

Create a PR:

```bash
curl -X POST http://127.0.0.1:8000/github/repos/acme-health/healthcare-backend/pulls \
  -H 'Content-Type: application/json' \
  -d '{"title":"PROJ-101 Add latest HbA1c report","body":"Implements latest HbA1c retrieval.","head":"feature/PROJ-101-hba1c-report","base":"main","idempotency_key":"PROJ-101-pr-v1"}'
```

## MCP tool contract

The supplied MCP server exposes tools equivalent to these REST operations:

- `jira_get_issue(issue_key)`
- `jira_list_issues()`
- `jira_update_issue(issue_key, status, fields)`
- `jira_add_comment(issue_key, comment)`
- `github_get_repository(owner, repo)`
- `github_list_files(owner, repo)`
- `github_read_file(owner, repo, path)`
- `github_create_branch(owner, repo, branch_name, from_branch)`
- `github_create_pull_request(owner, repo, title, body, head, base, idempotency_key)`
- `slack_send_message(channel, text)`
- `quality_scan(owner, repo)`

Tool names and schemas are discoverable via MCP `tools/list`. Invoke using MCP `tools/call`.

## Required behavior

1. Parse issue key and intent from the user request.
2. Fetch the Jira issue and acceptance criteria.
3. Resolve the repository from the issue's `repository` field and owner from `github_owner`.
4. Inspect repository metadata and relevant files; do not assume filenames.
5. Produce a structured implementation plan with files, changes, tests, risks, and assumptions.
6. Pause for explicit human approval before creating a branch, PR, Jira update, or notification.
7. Create a branch with a predictable name.
8. Create a PR. Use an idempotency key to prevent duplicates.
9. Add a Jira comment containing the PR URL and update status.
10. Return a concise execution summary with resource identifiers and any failures.

**Important:** This mock environment simulates branch and PR metadata; it does not modify a real GitHub repository or run Git operations. Your agent should not claim that source code was committed unless you implement a separate mock file-change operation and clearly report it as simulated.

## 2-hour suggested schedule

| Time | Deliverable |
|---|---|
| 0–15 min | Read contract, run mock API, inspect data |
| 15–35 min | Implement Jira + GitHub REST tools |
| 35–55 min | Implement MCP client adapter / discover tools |
| 55–80 min | Build LangGraph state and routing |
| 80–100 min | Add approval, branch/PR, Jira update |
| 100–115 min | Error handling, idempotency, tests |
| 115–120 min | README, run-through, explain architecture |

## Evaluation rubric (100 points)

| Area | Points |
|---|---:|
| REST integration and schemas | 12 |
| MCP discovery and invocation | 12 |
| LangGraph state and orchestration | 18 |
| Correct Jira-to-repository resolution | 10 |
| Approval gate before side effects | 12 |
| Branch / PR / Jira update workflow | 12 |
| Error handling, retry, idempotency | 10 |
| Tests, logging, code quality | 8 |
| Clear README and demo | 6 |

## Constraints and edge cases to handle

- Unknown Jira issue: return a useful not-found response; do not invent details.
- Missing repository mapping: ask for clarification or report the missing mapping.
- Empty acceptance criteria: identify the ambiguity; do not silently invent requirements.
- GitHub API failure: bounded retry with backoff; preserve workflow state.
- Duplicate PR request: return the existing PR when idempotency key matches.
- Approval denied: do not create branch, PR, Jira comment, or Slack message.
- Invalid status: return HTTP 422.
- Missing file path: return HTTP 404.
- External quality scan can return a warning; surface it in the plan.
- Do not expose API tokens or secrets in logs.

## What is intentionally not supplied

- No LangGraph graph implementation.
- No agent prompts or coordinator implementation.
- No MCP client orchestration code.
- No solution to the business workflow.
- No implementation-plan answer for PROJ-101.

You are expected to build these during the timed test.
