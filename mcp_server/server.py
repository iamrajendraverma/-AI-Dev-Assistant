"""MCP stdio adapter over the local mock REST API.

Run with: python -m mcp_server.server
This is an integration fixture, not an agent implementation.
"""
import asyncio
import httpx
from mcp.server.fastmcp import FastMCP

BASE = "http://127.0.0.1:8000"
mcp = FastMCP("mock-dev-platform")

async def request(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(base_url=BASE, timeout=8.0) as client:
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def jira_get_issue(issue_key: str) -> dict:
    """Get a Jira issue by key, including acceptance criteria and repository mapping."""
    return await request("GET", f"/jira/issues/{issue_key}")

@mcp.tool()
async def jira_list_issues() -> dict:
    """List all available mock Jira issues."""
    return await request("GET", "/jira/issues")

@mcp.tool()
async def jira_update_issue(issue_key: str, status: str = "", fields: dict | None = None) -> dict:
    """Update Jira issue status and/or additional fields."""
    payload = {"fields": fields or {}}
    if status:
        payload["status"] = status
    return await request("PATCH", f"/jira/issues/{issue_key}", json=payload)

@mcp.tool()
async def jira_add_comment(issue_key: str, comment: str) -> dict:
    """Add a comment to a Jira issue."""
    return await request("POST", f"/jira/issues/{issue_key}/comments", json={"comment": comment})

@mcp.tool()
async def github_get_repository(owner: str, repo: str) -> dict:
    """Get mock GitHub repository metadata."""
    return await request("GET", f"/github/repos/{owner}/{repo}")

@mcp.tool()
async def github_list_files(owner: str, repo: str) -> dict:
    """List files tracked in a mock GitHub repository."""
    return await request("GET", f"/github/repos/{owner}/{repo}/files")

@mcp.tool()
async def github_read_file(owner: str, repo: str, path: str) -> dict:
    """Read a file from a mock GitHub repository."""
    return await request("GET", f"/github/repos/{owner}/{repo}/file", params={"path": path})

@mcp.tool()
async def github_create_branch(owner: str, repo: str, branch_name: str, from_branch: str = "main") -> dict:
    """Create a simulated branch. Requires explicit user approval in the calling agent."""
    return await request("POST", f"/github/repos/{owner}/{repo}/branches",
                         json={"branch_name": branch_name, "from_branch": from_branch})

@mcp.tool()
async def github_create_pull_request(owner: str, repo: str, title: str, body: str,
                                     head: str, base: str = "main",
                                     idempotency_key: str = "") -> dict:
    """Create a simulated PR. Requires explicit user approval in the calling agent."""
    return await request("POST", f"/github/repos/{owner}/{repo}/pulls",
                         json={"title": title, "body": body, "head": head,
                               "base": base, "idempotency_key": idempotency_key})

@mcp.tool()
async def slack_send_message(channel: str, text: str) -> dict:
    """Send a simulated Slack message."""
    return await request("POST", "/slack/messages", json={"channel": channel, "text": text})

@mcp.tool()
async def quality_scan(owner: str, repo: str) -> dict:
    """Retrieve the pre-seeded mock quality scan for a repository."""
    return await request("GET", f"/external/quality/{owner}/{repo}")

if __name__ == "__main__":
    mcp.run(transport="stdio")
