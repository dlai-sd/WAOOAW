"""Marketing scheduled posting runner."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.content_models import ContentPost, DestinationRef, PublishInput, PublishReceipt
from agent_mold.skills.publisher_engine import default_engine
from core.database import get_connector
from models.publish_receipt import PublishReceiptModel
from services.draft_batches import DatabaseDraftBatchStore
from services.marketing_credential_resolver import resolve_youtube_secret_ref
from services.marketing_providers import default_social_provider, provider_allowlist
from services.usage_events import UsageEvent, UsageEventStore, UsageEventType


def _build_publish_input(
    *,
    batch,
    post,
    credential_ref: str | None,
) -> PublishInput:
    return PublishInput(
        post=ContentPost(
            post_id=post.post_id,
            campaign_id=batch.campaign_id or "",
            theme_item_id="",
            destination=DestinationRef(
                destination_type=post.channel.value,
                metadata={"customer_id": batch.customer_id or ""},
            ),
            content_text=post.text,
            hashtags=post.hashtags or [],
            scheduled_publish_at=post.scheduled_at or datetime.now(timezone.utc),
        ),
        credential_ref=credential_ref,
        approval_id=post.approval_id,
        visibility=post.visibility,
        public_release_requested=post.public_release_requested,
    )


def _persist_publish_receipt(session: AsyncSession, receipt: PublishReceipt) -> None:
    session.add(
        PublishReceiptModel(
            post_id=receipt.post_id,
            destination_type=receipt.destination_type,
            success=receipt.success,
            platform_post_id=receipt.platform_post_id,
            published_at=receipt.published_at,
            error=receipt.error,
            raw_response=receipt.raw_response,
        )
    )


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

                receipt_persisted = False
                try:
                    effective_credential_ref = await resolve_youtube_secret_ref(
                        session,
                        hired_instance_id=batch.hired_instance_id,
                        supplied_ref=post.credential_ref,
                    )

                    if fail_channel and post.channel.value == fail_channel:
                        raise RuntimeError(f"Simulated transient failure for channel={fail_channel}")

                    allowlist.ensure_allowed(post.channel)

                    if post.channel.value == "youtube":
                        publish_input = _build_publish_input(
                            batch=batch,
                            post=post,
                            credential_ref=effective_credential_ref,
                        )
                        receipt = await default_engine.publish(publish_input)
                        _persist_publish_receipt(session, receipt)
                        receipt_persisted = True
                        provider_post_id = receipt.platform_post_id
                        provider_post_url = (
                            receipt.raw_response.get("post_url")
                            if isinstance(receipt.raw_response, dict)
                            else None
                        )
                        if not receipt.success:
                            raise RuntimeError(receipt.error or "Publish failed via engine")
                    else:
                        published = provider.publish_text(
                            channel=post.channel,
                            text=post.text,
                            hashtags=post.hashtags,
                            credential_ref=post.credential_ref,
                        )
                        provider_post_id = published.provider_post_id
                        provider_post_url = published.provider_post_url
                        _persist_publish_receipt(
                            session,
                            PublishReceipt(
                                post_id=post.post_id,
                                destination_type=post.channel.value,
                                success=True,
                                platform_post_id=provider_post_id,
                                published_at=datetime.now(timezone.utc),
                                raw_response={"post_url": provider_post_url} if provider_post_url else None,
                            ),
                        )
                        receipt_persisted = True

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
                    if not receipt_persisted:
                        _persist_publish_receipt(
                            session,
                            PublishReceipt(
                                post_id=post.post_id,
                                destination_type=post.channel.value,
                                success=False,
                                error=str(exc),
                            ),
                        )
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
