from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_issue_tracker_api_dockerfile_pins_python_3_12_slim():
    dockerfile = REPO_ROOT / "docker" / "issue-tracker-api" / "Dockerfile"
    assert dockerfile.exists(), "docker/issue-tracker-api/Dockerfile is missing"
    content = dockerfile.read_text()
    assert "FROM python:3.12-slim" in content
    assert "latest" not in content.lower()


def test_issue_tracker_api_dockerfile_declares_healthcheck_and_reads_env():
    content = (REPO_ROOT / "docker" / "issue-tracker-api" / "Dockerfile").read_text()
    assert "HEALTHCHECK" in content
    assert "DATABASE_PATH" in content
    assert "PORT" in content
