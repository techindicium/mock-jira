from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_requirements_e2e_includes_mcp_sdk_via_requirements_mcp():
    content = (REPO_ROOT / "requirements-e2e.txt").read_text()
    assert "-r requirements-mcp.txt" in content, (
        "mcp e2e tests need the mcp SDK/httpx/anyio pinned in requirements-mcp.txt; "
        "include it rather than re-pinning them separately"
    )


def test_requirements_e2e_still_includes_playwright():
    content = (REPO_ROOT / "requirements-e2e.txt").read_text()
    assert "playwright" in content
