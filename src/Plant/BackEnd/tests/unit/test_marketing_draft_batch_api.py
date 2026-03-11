def test_create_draft_batch_persists_posts_and_returns_ids(db_test_client):
    payload = {
        "agent_id": "AGT-MKT-HEALTH-001",
        "hired_instance_id": "HIRED-001",
        "campaign_id": "CAM-001",
        "customer_id": "CUST-001",
        "theme": "5 quick tips for managing seasonal allergies",
        "brand_name": "Care Clinic",
        "brief_summary": "Seasonal allergy education for families in Pune via YouTube.",
        "offer": "Walk-in checkups available",
        "location": "Pune",
        "audience": "Families",
        "tone": "Calm and reassuring",
        "language": "English",
    }

    resp = db_test_client.post("/api/v1/marketing/draft-batches", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["batch_id"]
    assert data["agent_id"] == payload["agent_id"]
    assert data["hired_instance_id"] == payload["hired_instance_id"]
    assert data["campaign_id"] == payload["campaign_id"]
    assert data["customer_id"] == payload["customer_id"]
    assert data["brief_summary"] == payload["brief_summary"]
    assert data["status"] == "pending_review"
    assert data["workflow_state"] == "draft_ready_for_review"

    posts = data["posts"]
    assert len(posts) == 5  # default channels

    post_ids = [p["post_id"] for p in posts]
    assert len(set(post_ids)) == len(post_ids)
    assert all(p["review_status"] == "pending_review" for p in posts)
    assert all(p["execution_status"] == "not_scheduled" for p in posts)

    listed = db_test_client.get("/api/v1/marketing/draft-batches", params={"customer_id": payload["customer_id"]})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_execute_draft_post_requires_approval_id(db_test_client):
    create = db_test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Seasonal allergies awareness",
            "brand_name": "Care Clinic",
        },
    )
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    denied = db_test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "intent_action": "publish",
        },
    )
    assert denied.status_code == 403
    denied_body = denied.json()
    assert denied_body["reason"] == "approval_required"
    assert denied_body["correlation_id"]

    allowed = db_test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "intent_action": "publish",
            "approval_id": "APR-123",
        },
    )
    assert allowed.status_code == 200
    allowed_body = allowed.json()
    assert allowed_body["allowed"] is True
    assert allowed_body["post_id"] == post_id
