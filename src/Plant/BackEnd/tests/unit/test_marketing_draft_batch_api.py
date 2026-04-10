import pytest

from agent_mold.skills.playbook import ChannelName, GeneratedArtifactReference


def test_create_draft_batch_persists_posts_and_returns_ids(test_client, in_memory_marketing_draft_store):
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

    resp = test_client.post("/api/v1/marketing/draft-batches", json=payload)
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

    listed = test_client.get("/api/v1/marketing/draft-batches", params={"customer_id": payload["customer_id"]})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_execute_draft_post_requires_approval_id(test_client, in_memory_marketing_draft_store):
    create = test_client.post(
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

    denied = test_client.post(
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

    allowed = test_client.post(
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


def test_execute_approved_draft_post_uses_stored_approval_id_when_payload_missing(
    test_client, in_memory_marketing_draft_store
):
    create = test_client.post(
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

    approve = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-STORED-001"},
    )
    assert approve.status_code == 200

    execute = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "intent_action": "publish",
        },
    )
    assert execute.status_code == 200
    execute_body = execute.json()
    assert execute_body["allowed"] is True
    assert execute_body["post_id"] == post_id


def test_execute_approved_draft_post_rejects_mismatched_approval_id(
    test_client, in_memory_marketing_draft_store
):
    create = test_client.post(
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

    approve = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-STORED-001"},
    )
    assert approve.status_code == 200

    execute = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "intent_action": "publish",
            "approval_id": "APR-WRONG-001",
        },
    )
    assert execute.status_code == 403
    execute_body = execute.json()
    assert execute_body["reason"] == "approval_invalid"


def test_execute_youtube_draft_post_publishes_and_persists(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """Approved YouTube post with credential_ref publishes and persists receipt fields."""
    from integrations.social.base import SocialPostResult

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "theme": "Health tips for YouTube",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    posts = create.json()["posts"]
    yt_post = next(p for p in posts if p["channel"] == "youtube")
    post_id = yt_post["post_id"]

    approve_resp = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-YT-001"},
    )
    assert approve_resp.status_code == 200

    async def _fake_post_text(self, *, credential_ref, text, image_url=None):
        return SocialPostResult(
            success=True,
            platform="youtube",
            post_id="yt-post-abc123",
            post_url="https://www.youtube.com/post/yt-post-abc123",
        )

    import integrations.social.youtube_client as yt_module
    monkeypatch.setattr(yt_module.YouTubeClient, "post_text", _fake_post_text)

    resp = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-001",
            "intent_action": "publish",
            "approval_id": "APR-YT-001",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["allowed"] is True
    assert body["execution_status"] == "posted"
    assert body["provider_post_id"] == "yt-post-abc123"
    assert body["provider_post_url"] == "https://www.youtube.com/post/yt-post-abc123"

    found = in_memory_marketing_draft_store._batches
    updated_post = None
    for batch in found.values():
        for p in batch.posts:
            if p.post_id == post_id:
                updated_post = p
                break
    assert updated_post is not None
    assert updated_post.execution_status == "posted"
    assert updated_post.provider_post_id == "yt-post-abc123"


def test_create_draft_batch_resolves_attached_youtube_secret_ref(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    async def _fake_resolve(db, *, hired_instance_id, supplied_ref):
        assert hired_instance_id == "HIRED-001"
        assert supplied_ref == "cred-youtube-1"
        return "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"

    import api.v1.marketing_drafts as marketing_drafts_module

    monkeypatch.setattr(marketing_drafts_module, "resolve_youtube_secret_ref", _fake_resolve)

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "hired_instance_id": "HIRED-001",
            "customer_id": "CUST-001",
            "theme": "Health tips for YouTube",
            "brand_name": "Care Clinic",
            "youtube_credential_ref": "cred-youtube-1",
            "channels": ["youtube"],
        },
    )
    assert create.status_code == 200
    yt_post = create.json()["posts"][0]
    assert yt_post["credential_ref"] == "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"


def test_create_draft_batch_round_trips_artifact_metadata(test_client, in_memory_marketing_draft_store, monkeypatch):
    from agent_mold.skills.playbook import CanonicalMessage, ChannelVariant, MarketingMultiChannelOutput, SkillExecutionResult
    import api.v1.marketing_drafts as marketing_drafts_module

    artifact = GeneratedArtifactReference(
        artifact_type="video",
        uri="gs://waooaw-test/drafts/video-001.mp4",
        preview_uri="https://cdn.waooaw.test/video-001-preview.jpg",
        mime_type="video/mp4",
        metadata={"duration_seconds": 45, "generation_status": "ready"},
    )

    def _fake_execute(_playbook, inp):
        canonical = CanonicalMessage(
            theme=inp.theme,
            core_message="Video draft ready for review",
            call_to_action="Approve the video draft",
            generated_artifacts=[artifact],
        )
        variant = ChannelVariant(
            channel=ChannelName.YOUTUBE,
            text="Video draft ready for review",
            hashtags=["WAOOAW"],
            generated_artifacts=[artifact],
        )
        return SkillExecutionResult(
            playbook_id="MARKETING.MULTICHANNEL.POST.V1",
            output=MarketingMultiChannelOutput(
                canonical=canonical,
                variants=[variant],
                generated_artifacts=[artifact],
            ),
            debug={"executor": "fake"},
        )

    monkeypatch.setattr(marketing_drafts_module, "execute_marketing_multichannel_v1", _fake_execute)

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            "agent_id": "AGT-MKT-001",
            "hired_instance_id": "HIRED-ART-001",
            "campaign_id": "CAM-ART-001",
            "customer_id": "CUST-ART-001",
            "theme": "YouTube content sprint",
            "brand_name": "WAOOAW",
            "channels": ["youtube"],
        },
    )

    assert create.status_code == 200
    post = create.json()["posts"][0]
    assert post["artifact_type"] == "video"
    assert post["artifact_uri"] == "gs://waooaw-test/drafts/video-001.mp4"
    assert post["artifact_preview_uri"] == "https://cdn.waooaw.test/video-001-preview.jpg"
    assert post["artifact_mime_type"] == "video/mp4"
    assert post["artifact_metadata"]["generation_status"] == "ready"
    assert len(post["generated_artifacts"]) == 1
    assert post["generated_artifacts"][0]["artifact_type"] == "video"

    batch = next(iter(in_memory_marketing_draft_store._batches.values()))
    stored_post = batch.posts[0]
    assert stored_post.artifact_type == "video"
    assert stored_post.generated_artifacts[0].artifact_type.value == "video"
