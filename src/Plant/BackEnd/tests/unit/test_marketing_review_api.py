from __future__ import annotations


def test_list_and_approve_draft_post(test_client, tmp_path, monkeypatch):
    store_path = tmp_path / "draft_batches.jsonl"
    monkeypatch.setenv("DRAFT_BATCH_STORE_PATH", str(store_path))

    created = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Healthy habits",
            "brand_name": "Care Clinic",
        },
    )
    assert created.status_code == 200
    batch = created.json()
    assert batch["batch_id"]
    assert batch["posts"]

    listed = test_client.get("/api/v1/marketing/draft-batches", params={"customer_id": "CUST-001"})
    assert listed.status_code == 200
    batches = listed.json()
    assert len(batches) == 1
    post_id = batches[0]["posts"][0]["post_id"]

    approved = test_client.post(f"/api/v1/marketing/draft-posts/{post_id}/approve", json={})
    assert approved.status_code == 200
    body = approved.json()
    assert body["post_id"] == post_id
    assert body["review_status"] == "approved"
    assert body["approval_id"].startswith("APR-")

    reread = test_client.get(f"/api/v1/marketing/draft-batches/{batch['batch_id']}")
    assert reread.status_code == 200
    reread_body = reread.json()
    match = [p for p in reread_body["posts"] if p["post_id"] == post_id][0]
    assert match["review_status"] == "approved"
    assert match["approval_id"] == body["approval_id"]

    scheduled = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/schedule",
        json={
            "scheduled_at": "2026-02-06T00:00:00+00:00",
        },
    )
    assert scheduled.status_code == 200
    scheduled_body = scheduled.json()
    assert scheduled_body["post_id"] == post_id
    assert scheduled_body["execution_status"] == "scheduled"

    reread2 = test_client.get(f"/api/v1/marketing/draft-batches/{batch['batch_id']}")
    assert reread2.status_code == 200
    reread2_body = reread2.json()
    match2 = [p for p in reread2_body["posts"] if p["post_id"] == post_id][0]
    assert match2["execution_status"] == "scheduled"
    assert match2["scheduled_at"]
