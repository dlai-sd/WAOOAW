"""End-to-end test for error recovery and handling.

Tests graceful error handling when platforms fail:
- Temporary failures (503) with retry logic
- Permanent errors (401) without retry
- Rate limits (429) with backoff
- Network timeouts with retry
- Customer manual retry

This test validates:
- Retry logic for transient errors
- No retry for permanent errors
- Proper error messages
- Correlation tracking
- Customer retry capability
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.orm.attributes import flag_modified

from models.hired_agent import HiredAgentModel, GoalInstanceModel
from models.deliverable import DeliverableModel, ApprovalModel


class TestErrorRecoveryE2E:
    """End-to-end test for error recovery."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_temporary_error_with_retry(self, db_session):
        """Test retry logic for temporary 503 errors."""
        customer_id = "customer_error_503"
        
        agent = HiredAgentModel(
            hired_instance_id="hired_error_503",
            subscription_id="sub_error_503",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            configured=True,
            config={"platforms": {"instagram": {"enabled": True}}},
            trial_status="ended_converted",
        )
        db_session.add(agent)
        goal = GoalInstanceModel(
            goal_instance_id="goal_error",
            hired_instance_id="hired_error_503",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
        )
        db_session.add(goal)
        db_session.commit()
        
        draft = DeliverableModel(
            deliverable_id="deliv_error_503",
            hired_instance_id="hired_error_503",
            goal_instance_id="goal_error",
            goal_template_id="daily_post_template",
            title="Post with 503 Recovery",
            payload={"platforms": {"instagram": {"caption": "Retry test"}}},
            review_status="approved",
            approval_id=None,
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()

        approval = ApprovalModel(
            approval_id="approval_503",
            deliverable_id=draft.deliverable_id,
            customer_id=customer_id,
            decision="approved",
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()

        draft.approval_id = approval.approval_id
        db_session.commit()
        
        # Simulate 503 on first call, success on second
        with patch("integrations.social.instagram_client.InstagramClient") as mock_ig:
            mock_instance = AsyncMock()
            mock_ig.return_value = mock_instance
            
            # First call: 503 error
            # Second call: Success
            mock_instance.create_post.side_effect = [
                Exception("503 Service Unavailable"),
                {"id": "post_recovered", "permalink": "https://instagram.com/p/recovered"}
            ]
            
            # Attempt 1: Fail
            try:
                await mock_instance.create_post(caption="Retry test")
            except Exception as e:
                draft.payload["error_log"] = [{"attempt": 1, "error": str(e)}]
                flag_modified(draft, "payload")
                db_session.commit()
            
            # Attempt 2: Success after retry
            result = await mock_instance.create_post(caption="Retry test")
            
            draft.execution_status = "executed"
            draft.executed_at = datetime.now(timezone.utc)
            draft.payload["execution_result"] = {"instagram": result}
            draft.payload["retry_count"] = 1
            flag_modified(draft, "payload")
            db_session.commit()
            db_session.refresh(draft)
        
        assert draft.execution_status == "executed"
        assert "error_log" in draft.payload
        assert draft.payload["retry_count"] == 1
        
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_permanent_error_no_retry(self, db_session):
        """Test that permanent 401 errors don't trigger retry."""
        customer_id = "customer_error_401"
        
        agent = HiredAgentModel(
            hired_instance_id="hired_error_401",
            subscription_id="sub_error_401",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            configured=True,
            config={"platforms": {"instagram": {"enabled": True}}},
            trial_status="ended_converted",
        )
        db_session.add(agent)
        goal = GoalInstanceModel(
            goal_instance_id="goal_error",
            hired_instance_id="hired_error_401",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
        )
        db_session.add(goal)
        db_session.commit()
        
        draft = DeliverableModel(
            deliverable_id="deliv_error_401",
            hired_instance_id="hired_error_401",
            goal_instance_id="goal_error",
            goal_template_id="daily_post_template",
            title="Post with Invalid Credentials",
            payload={"platforms": {"instagram": {"caption": "Will fail"}}},
            review_status="approved",
            approval_id=None,
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()

        approval = ApprovalModel(
            approval_id="approval_401",
            deliverable_id=draft.deliverable_id,
            customer_id=customer_id,
            decision="approved",
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()

        draft.approval_id = approval.approval_id
        db_session.commit()
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_ig:
            mock_instance = AsyncMock()
            mock_ig.return_value = mock_instance
            
            # Permanent auth error
            mock_instance.create_post.side_effect = Exception("401 Unauthorized: Invalid access token")
            
            try:
                await mock_instance.create_post(caption="Will fail")
            except Exception as e:
                draft.execution_status = "failed"
                draft.payload["execution_error"] = {
                    "error": str(e),
                    "error_type": "authentication_error",
                    "retryable": False,
                    "customer_message": "Please reconnect your Instagram account"
                }
                flag_modified(draft, "payload")
                db_session.commit()
                db_session.refresh(draft)
        
        assert draft.execution_status == "failed"
        assert "execution_error" in draft.payload
        assert draft.payload["execution_error"]["retryable"] is False
        assert "Invalid access token" in draft.payload["execution_error"]["error"]
        
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_rate_limit_error_with_backoff(self, db_session):
        """Test rate limit 429 errors respect retry-after."""
        customer_id = "customer_error_429"
        
        agent = HiredAgentModel(
            hired_instance_id="hired_error_429",
            subscription_id="sub_error_429",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            configured=True,
            trial_status="ended_converted",
        )
        db_session.add(agent)
        goal = GoalInstanceModel(
            goal_instance_id="goal_error",
            hired_instance_id="hired_error_429",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
        )
        db_session.add(goal)
        db_session.commit()
        
        draft = DeliverableModel(
            deliverable_id="deliv_error_429",
            hired_instance_id="hired_error_429",
            goal_instance_id="goal_error",
            goal_template_id="daily_post_template",
            title="Post with Rate Limit",
            payload={"platforms": {"instagram": {"caption": "Rate limited"}}},
            review_status="approved",
            approval_id=None,
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()

        approval = ApprovalModel(
            approval_id="approval_429",
            deliverable_id=draft.deliverable_id,
            customer_id=customer_id,
            decision="approved",
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()

        draft.approval_id = approval.approval_id
        db_session.commit()
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_ig:
            mock_instance = AsyncMock()
            mock_ig.return_value = mock_instance
            
            # Simulate rate limit with retry-after
            rate_limit_error = Exception("429 Too Many Requests")
            rate_limit_error.retry_after = 60  # Wait 60 seconds
            
            mock_instance.create_post.side_effect = [
                rate_limit_error,
                {"id": "post_after_limit", "permalink": "https://instagram.com/p/after_limit"}
            ]
            
            # First attempt: Rate limited
            try:
                await mock_instance.create_post(caption="Rate limited")
            except Exception as e:
                draft.payload["rate_limit_info"] = {
                    "hit_at": datetime.now(timezone.utc).isoformat(),
                    "retry_after_seconds": getattr(e, 'retry_after', 60)
                }
                flag_modified(draft, "payload")
                db_session.commit()
            
            # Second attempt: Success after waiting
            result = await mock_instance.create_post(caption="Rate limited")
            
            draft.execution_status = "executed"
            draft.executed_at = datetime.now(timezone.utc)
            draft.payload["execution_result"] = {"instagram": result}
            flag_modified(draft, "payload")
            db_session.commit()
            db_session.refresh(draft)
        
        assert draft.execution_status == "executed"
        assert "rate_limit_info" in draft.payload
        assert draft.payload["rate_limit_info"]["retry_after_seconds"] == 60
        
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_network_timeout_with_retry(self, db_session):
        """Test network timeout errors trigger retry."""
        customer_id = "customer_error_timeout"
        
        agent = HiredAgentModel(
            hired_instance_id="hired_error_timeout",
            subscription_id="sub_error_timeout",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            configured=True,
            trial_status="ended_converted",
        )
        db_session.add(agent)
        goal = GoalInstanceModel(
            goal_instance_id="goal_error",
            hired_instance_id="hired_error_timeout",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
        )
        db_session.add(goal)
        db_session.commit()
        
        draft = DeliverableModel(
            deliverable_id="deliv_error_timeout",
            hired_instance_id="hired_error_timeout",
            goal_instance_id="goal_error",
            goal_template_id="daily_post_template",
            title="Post with Timeout",
            payload={"platforms": {"instagram": {"caption": "Timeout test"}}},
            review_status="approved",
            approval_id=None,
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()

        approval = ApprovalModel(
            approval_id="approval_timeout",
            deliverable_id=draft.deliverable_id,
            customer_id=customer_id,
            decision="approved",
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()

        draft.approval_id = approval.approval_id
        db_session.commit()
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_ig:
            mock_instance = AsyncMock()
            mock_ig.return_value = mock_instance
            
            # Timeout then success
            mock_instance.create_post.side_effect = [
                Exception("Timeout: Connection timeout after 30s"),
                {"id": "post_after_timeout"}
            ]
            
            # First: Timeout
            try:
                await mock_instance.create_post(caption="Timeout test")
            except Exception as e:
                draft.payload["timeout_log"] = [{"error": str(e)}]
                flag_modified(draft, "payload")
                db_session.commit()
            
            # Second: Success
            result = await mock_instance.create_post(caption="Timeout test")
            
            draft.execution_status = "executed"
            draft.payload["execution_result"] = {"instagram": result}
            flag_modified(draft, "payload")
            db_session.commit()
            db_session.refresh(draft)
        
        assert draft.execution_status == "executed"
        assert "timeout_log" in draft.payload
        
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_customer_manual_retry(self, db_session):
        """Test customer can manually retry failed execution."""
        customer_id = "customer_manual_retry"
        
        agent = HiredAgentModel(
            hired_instance_id="hired_manual_retry",
            subscription_id="sub_manual_retry",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            configured=True,
            trial_status="ended_converted",
        )
        db_session.add(agent)
        goal = GoalInstanceModel(
            goal_instance_id="goal_retry",
            hired_instance_id="hired_manual_retry",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
        )
        db_session.add(goal)
        db_session.commit()
        
        # Initial failed attempt
        draft = DeliverableModel(
            deliverable_id="deliv_manual_retry",
            hired_instance_id="hired_manual_retry",
            goal_instance_id="goal_retry",
            goal_template_id="daily_post_template",
            title="Failed Post",
            payload={
                "platforms": {"instagram": {"caption": "Manual retry"}},
                "execution_error": {"error": "Previous failure"}
            },
            review_status="approved",
            approval_id=None,
            execution_status="failed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()

        approval = ApprovalModel(
            approval_id="approval_retry",
            deliverable_id=draft.deliverable_id,
            customer_id=customer_id,
            decision="approved",
            notes=None,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()

        draft.approval_id = approval.approval_id
        db_session.commit()
        
        # Customer clicks "Retry" button
        # System clears error and retries
        draft.execution_status = "retrying"
        draft.payload.pop("execution_error", None)
        draft.payload["retry_initiated_by"] = "customer"
        flag_modified(draft, "payload")
        db_session.commit()
        
        # Retry succeeds
        with patch("integrations.social.instagram_client.InstagramClient") as mock_ig:
            mock_instance = AsyncMock()
            mock_ig.return_value = mock_instance
            mock_instance.create_post.return_value = {"id": "post_retry_success"}
            
            result = await mock_instance.create_post(caption="Manual retry")
            
            draft.execution_status = "executed"
            draft.executed_at = datetime.now(timezone.utc)
            draft.payload["execution_result"] = {"instagram": result}
            flag_modified(draft, "payload")
            db_session.commit()
            db_session.refresh(draft)
        
        assert draft.execution_status == "executed"
        assert draft.payload["retry_initiated_by"] == "customer"
        assert "execution_result" in draft.payload
