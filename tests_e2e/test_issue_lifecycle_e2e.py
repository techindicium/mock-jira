import httpx


def test_full_issue_lifecycle_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        project = client.post(
            "/projects", json={"key": "E2ELIFE", "name": "E2E Lifecycle Project"}
        ).json()

        created = client.post(
            "/issues",
            json={
                "project_id": project["id"], "summary": "e2e issue",
                "issue_type": "task", "priority": "medium",
            },
        ).json()
        issue_id = created["id"]
        assert created["status"] == "todo"

        listed = client.get("/issues", params={"project_id": project["id"]}).json()
        assert any(i["id"] == issue_id for i in listed)

        fetched = client.get(f"/issues/{issue_id}").json()
        assert fetched["id"] == issue_id

        patched = client.patch(f"/issues/{issue_id}", json={"status": "in_progress"}).json()
        assert patched["status"] == "in_progress"
        patched = client.patch(f"/issues/{issue_id}", json={"status": "done"}).json()
        assert patched["status"] == "done"

        delete_resp = client.delete(f"/issues/{issue_id}")
        assert delete_resp.status_code == 204

        gone_resp = client.get(f"/issues/{issue_id}")
        assert gone_resp.status_code == 404
        assert gone_resp.json()["code"] == "ISSUE_NOT_FOUND"
