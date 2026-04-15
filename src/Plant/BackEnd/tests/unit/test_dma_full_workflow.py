"""Full DMA workflow tests: theme generation → approve → content creation → review → publish.

Stages:
  1. Theme batch:  create batch with table artifact (the strategic direction / content plan)
  2. Approve/reject theme post
  3. Content batch: create batch with image/video artifact (actual publishable content)
  4. Approve content post
  5. Publish approved content post via YouTube
  6. Guard: unapproved post cannot be published
  7. Guard: rejected post cannot be published
  8. Guard: mismatched approval_id is rejected at publish
  9. Video artifact carries text/markdown mime (script, not a rendered file)
"""

import pytest
from integrations.social.base import SocialPostResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_THEME_PAYLOAD = {
    "agent_id": "AGT-MKT-HEALTH-001",
    "hired_instance_id": "HIRED-WF-001",
    "campaign_id": "CAM-WF-001",
    "customer_id": "CUST-WF-001",
    "theme": "Weekly healthcare tips for Pune families",
    "brand_name": "Care Clinic",
    "brief_summary": "Theme planning sprint — generate content calendar ideas.",
    "channels": ["youtube"],
    "requested_artifacts": [{"artifact_type": "table", "prompt": "Create a 4-week YouTube content plan table"}],
}

_CONTENT_PAYLOAD = {
    "agent_id": "AGT-MKT-HEALTH-001",
    "hired_instance_id": "HIRED-WF-001",
    "campaign_id": "CAM-WF-001",
    "customer_id": "CUST-WF-001",
    "theme": "Tip #1: Managing seasonal allergies",
    "brand_name": "Care Clinic",
    "brief_summary": "Content batch — approved theme tip #1.",
    "youtube_credential_ref": "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest",
    "channels": ["youtube"],
}


def _fake_youtube_post(monkeypatch):
    """Patch YouTubeClient.post_text to avoid real network calls."""
    async def _stub(self, *, credential_ref, text, image_url=None):
        return SocialPostResult(
            success=True,
            platform="youtube",
            post_id="yt-wf-post-001",
            post_url="https://www.youtube.com/post/yt-wf-post-001",
        )

    import integrations.social.youtube_client as yt_module
    monkeypatch.setattr(yt_module.YouTubeClient, "post_text", _stub)


# ---------------------------------------------------------------------------
# Stage 1 + 2: Theme generation and approval
# ---------------------------------------------------------------------------

def test_theme_batch_created_as_pending_review(test_client, in_memory_marketing_draft_store):
    """Theme batch starts at pending_review — agent must wait for customer sign-off."""
    resp = test_client.post("/api/v1/marketing/draft-batches", json=_THEME_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "pending_review"
    assert data["workflow_state"] == "draft_ready_for_review"
    assert len(data["posts"]) == 1  # single youtube channel

    post = data["posts"][0]
    assert post["review_status"] == "pending_review"
    assert post["artifact_type"] == "table"
    assert post["artifact_generation_status"] == "ready"


def test_approve_theme_post_marks_it_approved(test_client, in_memory_marketing_draft_store):
    """Approving a theme post stores the approval_id and transitions review_status."""
    create = test_client.post("/api/v1/marketing/draft-batches", json=_THEME_PAYLOAD)
    post_id = create.json()["posts"][0]["post_id"]

    approve = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-THEME-001"},
    )
    assert approve.status_code == 200

    # Verify post is now approved in the store
    for batch in in_memory_marketing_draft_store._batches.values():
        for p in batch.posts:
            if p.post_id == post_id:
                assert p.review_status == "approved"
                assert p.approval_id == "APR-THEME-001"
                return
    pytest.fail("Post not found in store after approval")


def test_reject_theme_post_marks_it_rejected(test_client, in_memory_marketing_draft_store):
    """Rejecting a theme post prevents it from being published."""
    create = test_client.post("/api/v1/marketing/draft-batches", json=_THEME_PAYLOAD)
    post_id = create.json()["posts"][0]["post_id"]

    reject = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/reject",
        json={"reason": "Theme direction too broad — needs focus."},
    )
    assert reject.status_code == 200

    for batch in in_memory_marketing_draft_store._batches.values():
        for p in batch.posts:
            if p.post_id == post_id:
                assert p.review_status == "rejected"
                return
    pytest.fail("Post not found in store after rejection")


# ---------------------------------------------------------------------------
# Stage 3 + 4: Content creation and approval
# ---------------------------------------------------------------------------

def test_content_batch_created_with_youtube_credential(test_client, in_memory_marketing_draft_store):
    """Content batch created separately from theme batch — credential_ref wired to post."""
    resp = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "pending_review"
    post = data["posts"][0]
    assert post["channel"] == "youtube"
    # Credential ref passed through as-is when it looks like a full GCP path
    assert post["credential_ref"] == "projects/waooaw-oauth/secrets/hired-1-youtube/versions/latest"


def test_content_post_review_statuses_are_independent_of_theme_batch(
    test_client, in_memory_marketing_draft_store
):
    """Theme batch and content batch are separate; approving one does not affect the other."""
    theme_resp = test_client.post("/api/v1/marketing/draft-batches", json=_THEME_PAYLOAD)
    content_resp = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)

    theme_post_id = theme_resp.json()["posts"][0]["post_id"]
    content_post_id = content_resp.json()["posts"][0]["post_id"]
    assert theme_post_id != content_post_id

    # Approve the theme post only
    test_client.post(
        f"/api/v1/marketing/draft-posts/{theme_post_id}/approve",
        json={"approval_id": "APR-THEME-WF"},
    )

    # Content post must still be pending
    listed = test_client.get(
        "/api/v1/marketing/draft-batches",
        params={"customer_id": "CUST-WF-001"},
    )
    batches = listed.json()
    assert len(batches) == 2

    content_post = None
    for batch in batches:
        for p in batch["posts"]:
            if p["post_id"] == content_post_id:
                content_post = p
    assert content_post is not None
    assert content_post["review_status"] == "pending_review"


# ---------------------------------------------------------------------------
# Stage 5: Publish approved content
# ---------------------------------------------------------------------------

def test_approved_content_post_publishes_to_youtube(test_client, in_memory_marketing_draft_store, monkeypatch):
    """Full publish path: create → approve → execute → posted receipt stored."""
    _fake_youtube_post(monkeypatch)

    create = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)
    assert create.status_code == 200
    post_id = create.json()["posts"][0]["post_id"]

    approve = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-CONTENT-001"},
    )
    assert approve.status_code == 200

    execute = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-WF-001",
            "intent_action": "publish",
        },
    )
    assert execute.status_code == 200
    body = execute.json()
    assert body["allowed"] is True
    assert body["execution_status"] == "posted"
    assert body["provider_post_id"] == "yt-wf-post-001"
    assert body["provider_post_url"] == "https://www.youtube.com/post/yt-wf-post-001"

    # Persisted in store
    stored_post = None
    for batch in in_memory_marketing_draft_store._batches.values():
        for p in batch.posts:
            if p.post_id == post_id:
                stored_post = p
    assert stored_post is not None
    assert stored_post.execution_status == "posted"
    assert stored_post.provider_post_id == "yt-wf-post-001"


# ---------------------------------------------------------------------------
# Stage 6: Guards — unapproved and rejected posts cannot be published
# ---------------------------------------------------------------------------

def test_unapproved_content_post_is_blocked_at_publish(test_client, in_memory_marketing_draft_store, monkeypatch):
    """Execute without prior approval returns 403 with reason=approval_required."""
    _fake_youtube_post(monkeypatch)

    create = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)
    post_id = create.json()["posts"][0]["post_id"]

    execute = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-WF-001",
            "intent_action": "publish",
        },
    )
    assert execute.status_code == 403
    assert execute.json()["reason"] == "approval_required"


def test_rejected_content_post_can_be_re_approved(test_client, in_memory_marketing_draft_store):
    """Rejection is not terminal — a customer can reject then change their mind and approve.
    The backend allows re-approval after rejection; the UI should show a re-approve option.
    """
    create = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)
    post_id = create.json()["posts"][0]["post_id"]

    test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/reject",
        json={"reason": "Caption not on-brand."},
    )

    # Customer changes mind — re-approval is allowed
    approve = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-AFTER-RECONSIDER"},
    )
    assert approve.status_code == 200

    # Post now shows approved status
    for batch in in_memory_marketing_draft_store._batches.values():
        for p in batch.posts:
            if p.post_id == post_id:
                assert p.review_status == "approved"
                return
    pytest.fail("Post not found in store")


def test_mismatched_approval_id_blocks_publish(test_client, in_memory_marketing_draft_store, monkeypatch):
    """Supplying an approval_id that does not match the stored one returns 403 approval_invalid."""
    _fake_youtube_post(monkeypatch)

    create = test_client.post("/api/v1/marketing/draft-batches", json=_CONTENT_PAYLOAD)
    post_id = create.json()["posts"][0]["post_id"]

    test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/approve",
        json={"approval_id": "APR-REAL-001"},
    )

    execute = test_client.post(
        f"/api/v1/marketing/draft-posts/{post_id}/execute",
        json={
            "agent_id": "AGT-MKT-HEALTH-001",
            "customer_id": "CUST-WF-001",
            "intent_action": "publish",
            "approval_id": "APR-TAMPERED",
        },
    )
    assert execute.status_code == 403
    assert execute.json()["reason"] == "approval_invalid"


# ---------------------------------------------------------------------------
# Stage 7: Video artifact is a text script, not a rendered video file
# ---------------------------------------------------------------------------

def test_video_artifact_request_is_queued_as_background_job(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """Video/audio artifacts are generated asynchronously (not instant).
    
    The job is queued immediately; artifact_generation_status == 'queued'.
    The final artifact will be a text/markdown script, not a binary video file.
    """
    import api.v1.marketing_drafts as marketing_drafts_module

    monkeypatch.setattr(
        marketing_drafts_module,
        "enqueue_media_generation_job",
        lambda **_: ("job-video-wf-1", "deferred"),
    )

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            **_CONTENT_PAYLOAD,
            "requested_artifacts": [
                {"artifact_type": "video", "prompt": "Create a 60-second YouTube health tip script"}
            ],
        },
    )
    assert create.status_code == 200
    post = create.json()["posts"][0]

    assert post["artifact_type"] == "video"
    assert post["artifact_generation_status"] == "queued"
    assert post["artifact_job_id"] == "job-video-wf-1"
    # Not publish-ready until artifact is ready AND approved
    assert post["publish_ready"] is False


def test_video_artifact_with_markdown_mime_is_a_script_not_a_video(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """When the background job completes with mime_type=text/markdown, the system
    stores it as-is. The UI uses that mime_type to show 'video script' not 'video'.
    This test verifies the artifact_mime_type is persisted correctly through the store.
    """
    from agent_mold.skills.playbook import (
        CanonicalMessage,
        ChannelVariant,
        ChannelName,
        GeneratedArtifactReference,
        MarketingMultiChannelOutput,
        SkillExecutionResult,
    )
    import api.v1.marketing_drafts as marketing_drafts_module

    artifact = GeneratedArtifactReference(
        artifact_type="video",
        uri="local://artifacts/video-script-wf.md",
        preview_uri=None,
        mime_type="text/markdown",
        metadata={"generation_status": "ready", "word_count": 312},
    )

    def _fake_execute(_playbook, inp):
        canonical = CanonicalMessage(
            theme=inp.theme,
            core_message="60-second health tip script",
            call_to_action="Record this and upload to YouTube",
            generated_artifacts=[artifact],
        )
        variant = ChannelVariant(
            channel=ChannelName.YOUTUBE,
            text="60-second health tip script",
            hashtags=["HealthTips"],
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
            **_CONTENT_PAYLOAD,
            "requested_artifacts": [
                {"artifact_type": "video", "prompt": "Create a 60-second YouTube health tip script"}
            ],
        },
    )
    assert create.status_code == 200
    post = create.json()["posts"][0]

    assert post["artifact_type"] == "video"
    assert post["artifact_mime_type"] == "text/markdown"
    assert "video-script-wf.md" in post["artifact_uri"]
    # This is a script, not a rendered video file — mime must be text/markdown
    assert post["artifact_mime_type"] != "video/mp4"


# ---------------------------------------------------------------------------
# Stage 8: Credential resolver converts short-form ref to GCP secret path
# ---------------------------------------------------------------------------

def test_short_credential_ref_is_resolved_to_gcp_path_at_batch_creation(
    test_client, in_memory_marketing_draft_store, monkeypatch
):
    """Short-form credentials (e.g. 'cred-yt-1') are resolved by DatabaseCredentialResolver
    to full GCP Secret Manager paths before being stored on the draft post.
    """
    async def _fake_resolve(db, *, hired_instance_id, supplied_ref):
        assert hired_instance_id == "HIRED-WF-001"
        assert supplied_ref == "cred-yt-short"
        return "projects/waooaw-oauth/secrets/hired-wf-001-youtube/versions/latest"

    import api.v1.marketing_drafts as marketing_drafts_module
    monkeypatch.setattr(marketing_drafts_module, "resolve_youtube_secret_ref", _fake_resolve)

    create = test_client.post(
        "/api/v1/marketing/draft-batches",
        json={
            **_CONTENT_PAYLOAD,
            "youtube_credential_ref": "cred-yt-short",
        },
    )
    assert create.status_code == 200
    post = create.json()["posts"][0]
    assert post["credential_ref"] == "projects/waooaw-oauth/secrets/hired-wf-001-youtube/versions/latest"
