"""Marketing scheduled posting runner."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_connector
from services.draft_batches import DatabaseDraftBatchStore
from services.marketing_credential_resolver import resolve_youtube_secret_ref
from services.marketing_providers import default_social_provider, provider_allowlist
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType


async def run_due_posts_once(
    now: datetime | None = None,
    usage_events: UsageEventStore | None = None,
    db: AsyncSession | None = None,
) -> int:
    now = now or datetime.utcnow()
    owns_session = db is None
    session = db or await get_connector().get_session()
    store = DatabaseDraftBatchStore(session)

    max_attempts = int(os.getenv("MARKETING_SCHEDULER_MAX_ATTEMPTS", "3"))
    fail_channel = os.getenv("MARKETING_FAKE_FAIL_CHANNEL")

    allowlist = provider_allowlist()
    provider = default_social_provider()

    batches = await store.load_batches()
    executed = 0
    updated = False

    try:
        for batch in batches:
            for post in batch.posts:
                if post.review_status != "approved":
                    continue
                if post.execution_status not in {"scheduled", "failed"}:
                    continue
                if post.scheduled_at is None or post.scheduled_at > now:
                    continue
                if post.attempts >= max_attempts:
                    continue

                attempt_count = post.attempts + 1
                await store.update_post(
                    post.post_id,
                    execution_status="running",
                    attempts=attempt_count,
                )

                try:
                    effective_credential_ref = await resolve_youtube_secret_ref(
                        session,
                        hired_instance_id=batch.hired_instance_id,
                        supplied_ref=post.credential_ref,
                    )
                    if post.channel.value == "youtube" and not post.approval_id:
                        raise RuntimeError("approval_required_for_youtube_publish")
                    if post.channel.value == "youtube" and not effective_credential_ref:
                        raise RuntimeError("credential_ref_required_for_youtube_publish")
                    if post.channel.value == "youtube" and post.visibility == "public" and not post.public_release_requested:
                        raise RuntimeError("public_release_requires_explicit_customer_action")

                    if fail_channel and post.channel.value == fail_channel:
                        raise RuntimeError(f"Simulated transient failure for channel={fail_channel}")

                    allowlist.ensure_allowed(post.channel)

                    if post.channel.value == "youtube" and post.credential_ref:
                        from integrations.social.youtube_client import YouTubeClient

                        yt_client = YouTubeClient(customer_id=batch.customer_id)
                        yt_result = await yt_client.post_text(
                            credential_ref=effective_credential_ref,
                            text=post.text,
                        )
                        provider_post_id = yt_result.post_id
                        provider_post_url = yt_result.post_url
                    else:
                        published = provider.publish_text(
                            channel=post.channel,
                            text=post.text,
                            hashtags=post.hashtags,
                            credential_ref=post.credential_ref,
                        )
                        provider_post_id = published.provider_post_id
                        provider_post_url = published.provider_post_url

                    await store.update_post(
                        post.post_id,
                        credential_ref=effective_credential_ref,
                        execution_status="posted",
                        attempts=attempt_count,
                        last_error=None,
                        provider_post_id=provider_post_id,
                        provider_post_url=provider_post_url,
                    )

                    if usage_events is not None:
                        usage_events.append(
                            UsageEvent(
                                event_type=UsageEventType.PUBLISH_ACTION,
                                correlation_id=f"draft_post:{post.post_id}",
                                customer_id=batch.customer_id,
                                agent_id=batch.agent_id,
                                purpose="marketing_publish",
                            )
                        )
                except Exception as exc:
                    await store.update_post(
                        post.post_id,
                        execution_status="failed",
                        attempts=attempt_count,
                        last_error=str(exc),
                    )

                executed += 1
                updated = True

        if owns_session and updated:
            await session.commit()

        return executed
    finally:
        if owns_session:
            await session.close()
