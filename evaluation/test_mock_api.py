"""Contract tests for the supplied mock APIs. Run after starting uvicorn."""
import pytest
import httpx

BASE = "http://127.0.0.1:8000"

@pytest.fixture
def client():
    return httpx.Client(base_url=BASE, timeout=5)

def test_health(client):
    assert client.get("/health").status_code == 200

def test_jira_issue_has_repo_mapping(client):
    response = client.get("/jira/issues/PROJ-101")
    assert response.status_code == 200
    data = response.json()
    assert data["repository"] == "healthcare-backend"
    assert data["github_owner"] == "acme-health"
    assert len(data["acceptance_criteria"]) >= 3

def test_unknown_issue_returns_404(client):
    assert client.get("/jira/issues/PROJ-999").status_code == 404

def test_invalid_status_returns_422(client):
    response = client.patch("/jira/issues/PROJ-101", json={"status": "FinishedMaybe"})
    assert response.status_code == 422

def test_repository_files_and_read(client):
    listing = client.get("/github/repos/acme-health/healthcare-backend/files")
    assert listing.status_code == 200
    assert "lab_service.py" in listing.json()["files"]
    file_response = client.get(
        "/github/repos/acme-health/healthcare-backend/file",
        params={"path": "lab_service.py"}
    )
    assert file_response.status_code == 200
    assert "latest_hba1c" in file_response.json()["content"]

def test_unknown_file_returns_404(client):
    response = client.get(
        "/github/repos/acme-health/healthcare-backend/file",
        params={"path": "secrets.env"}
    )
    assert response.status_code == 404

def test_branch_then_idempotent_pr(client):
    branch = "feature/PROJ-TEST-idempotency"
    created = client.post(
        "/github/repos/acme-health/healthcare-backend/branches",
        json={"branch_name": branch, "from_branch": "main"}
    )
    assert created.status_code == 201
    payload = {
        "title": "Test PR", "body": "test", "head": branch, "base": "main",
        "idempotency_key": "evaluation-test-key"
    }
    first = client.post("/github/repos/acme-health/healthcare-backend/pulls", json=payload)
    second = client.post("/github/repos/acme-health/healthcare-backend/pulls", json=payload)
    assert first.status_code == 201 and first.json()["created"] is True
    assert second.status_code == 201 and second.json()["created"] is False
    assert first.json()["html_url"] == second.json()["html_url"]

def test_pr_requires_existing_branch(client):
    response = client.post(
        "/github/repos/acme-health/healthcare-backend/pulls",
        json={
            "title": "Invalid PR", "body": "", "head": "missing-branch",
            "base": "main", "idempotency_key": "invalid-branch-test"
        }
    )
    assert response.status_code == 422

def test_external_quality_scan(client):
    response = client.get("/external/quality/acme-health/healthcare-backend")
    assert response.status_code == 200
    assert response.json()["quality_gate"] == "passed"
