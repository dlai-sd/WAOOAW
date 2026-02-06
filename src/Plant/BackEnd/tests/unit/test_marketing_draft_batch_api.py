def test_create_draft_batch_persists_posts_and_returns_ids(test_client, tmp_path, monkeypatch):
    store_path = tmp_path / "draft_batches.jsonl"
    monkeypatch.setenv("DRAFT_BATCH_STORE_PATH", str(store_path))

    payload = {
        "agent_id": "AGT-MKT-HEALTH-001",
        "customer_id": "CUST-001",
        "theme": "5 quick tips for managing seasonal allergies",
        "brand_name": "Care Clinic",
        "offer": "Walk-in checkups available",
        "location": "Pune",
        "audience": "Families",
        "tone": "Calm and reassuring",
        "language": "English",
    }

    resp = test_client.post("/api/v1/marketing/draft-batches", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["batch_id"]
    assert data["agent_id"] == payload["agent_id"]
    assert data["customer_id"] == payload["customer_id"]
    assert data["status"] == "pending_review"

    posts = data["posts"]
    assert len(posts) == 5  # default channels

    post_ids = [p["post_id"] for p in posts]
    assert len(set(post_ids)) == len(post_ids)
    assert all(p["review_status"] == "pending_review" for p in posts)
    assert all(p["execution_status"] == "not_scheduled" for p in posts)

    assert store_path.exists()
    lines = store_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "\"batch_id\"" in lines[0]
