"""End-to-end test for trial limits enforcement.

Tests that trial limitations are properly enforced throughout agent workflows:
- Daily task cap (10 tasks/day)
- High-cost call blocking (>$1/call)
- Production write blocking (intent actions)
- Upgrade path (convert to paid removes restrictions)

This test validates:
- Trial agent creation and configuration
- Trial limit enforcement via metering service
- Upgrade to paid subscription
- Limit removal after upgrade
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy.orm.attributes import flag_modified

from models.hired_agent import HiredAgentModel, GoalInstanceModel
from models.deliverable import DeliverableModel, ApprovalModel
from core.exceptions import UsageLimitError
from services.metering import enforce_trial_and_budget
from services.usage_events import InMemoryUsageEventStore
from services.usage_ledger import InMemoryUsageLedger


class TestTrialLimitsE2E:
    """End-to-end test for trial limits enforcement."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_trial_limits_enforcement_workflow(self, db_session):
        """Test complete trial limits enforcement workflow.
        
        Workflow:
        1. Create trial agent
        2. Configure agent (should succeed)
        3. Trigger 10 goal runs (should succeed)
        4. 11th run denied with trial_daily_cap
        5. Attempt high-cost operation (denied)
        6. Attempt production write (denied)
        7. Upgrade to paid
        8. Production write succeeds
        """
        customer_id = "customer_trial_limits"
        
        # Initialize metering infrastructure
        ledger = InMemoryUsageLedger()
        events = InMemoryUsageEventStore()
        
        # ====================================================================
        # Step 1: Create Trial Agent
        # ====================================================================
        
        trial_agent = HiredAgentModel(
            hired_instance_id="hired_trial_limits",
            subscription_id="sub_trial_limits",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            nickname="Trial Marketing Agent",
            theme="professional",
            config={},
            configured=False,
            trial_status="active",  # Trial mode active
            trial_start_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trial_agent)
        db_session.commit()
        db_session.refresh(trial_agent)
        
        assert trial_agent.trial_status == "active"
        assert trial_agent.trial_start_at is not None
        
        # ====================================================================
        # Step 2: Configure Agent (Trial Allows Configuration)
        # ====================================================================
        
        trial_agent.config = {
            "timezone": "America/New_York",
            "brand_name": "Trial Brand",
            "platforms": {
                "instagram": {
                    "enabled": True,
                    "account_id": "trial_instagram",
                    "access_token": "trial_token",
                },
            },
        }
        trial_agent.configured = True
        db_session.commit()
        db_session.refresh(trial_agent)
        
        assert trial_agent.configured is True
        
        # ====================================================================
        # Step 3: Trigger 10 Goal Runs (Trial Daily Cap = 10)
        # ====================================================================
        
        # Create a goal for the trial agent
        trial_goal = GoalInstanceModel(
            goal_instance_id="goal_trial_limits",
            hired_instance_id="hired_trial_limits",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={
                "platforms": ["instagram"],
                "content_type": "image",
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trial_goal)
        db_session.commit()
        
        # Simulate 10 goal runs (should all succeed)
        now = datetime.now(timezone.utc)
        
        for i in range(10):
            # Each goal run triggers metering enforcement
            enforce_trial_and_budget(
                correlation_id=f"corr_trial_{i}",
                agent_id=trial_agent.agent_id,
                customer_id=customer_id,
                plan_id=None,
                trial_mode=True,  # Trial mode active
                intent_action=None,  # No production write yet
                effective_estimated_cost_usd=0.5,  # Within $1 limit
                meter_tokens_in=100,
                meter_tokens_out=200,
                purpose="trial_goal_run",
                ledger=ledger,
                events=events,
                now=now,
            )
        
        # Verify all 10 runs succeeded (no exception raised)
        assert True  # If we got here, all 10 runs passed
        
        # ====================================================================
        # Step 4: 11th Run Denied with trial_daily_cap Error
        # ====================================================================
        
        with pytest.raises(UsageLimitError) as excinfo:
            enforce_trial_and_budget(
                correlation_id="corr_trial_11",
                agent_id=trial_agent.agent_id,
                customer_id=customer_id,
                plan_id=None,
                trial_mode=True,
                intent_action=None,
                effective_estimated_cost_usd=0.5,
                meter_tokens_in=100,
                meter_tokens_out=200,
                purpose="trial_goal_run",
                ledger=ledger,
                events=events,
                now=now,
            )
        
        error = excinfo.value
        assert error.reason == "trial_daily_cap"
        assert "10 tasks/day" in str(error)
        assert error.details["limit"] == 10
        assert "window_resets_at" in error.details
        
        # ====================================================================
        # Step 5: Attempt High-Cost Operation (>$1/call)
        # ====================================================================
        
        # Reset ledger for next day (simulate day boundary)
        ledger_new_day = InMemoryUsageLedger()
        events_new_day = InMemoryUsageEventStore()
        
        with pytest.raises(UsageLimitError) as excinfo:
            enforce_trial_and_budget(
                correlation_id="corr_high_cost",
                agent_id=trial_agent.agent_id,
                customer_id=customer_id,
                plan_id=None,
                trial_mode=True,
                intent_action=None,
                effective_estimated_cost_usd=2.0,  # Exceeds $1 trial limit
                meter_tokens_in=10000,
                meter_tokens_out=20000,
                purpose="high_cost_operation",
                ledger=ledger_new_day,
                events=events_new_day,
                now=now,
            )
        
        error = excinfo.value
        assert error.reason == "trial_high_cost_call"
        assert ">$1/call" in str(error)
        assert error.details["estimated_cost_usd"] == 2.0
        assert error.details["max_cost_usd"] == 1.0
        
        # ====================================================================
        # Step 6: Attempt Production Write (intent_action set)
        # ====================================================================
        
        # Create a draft deliverable for production write (without approval_id first)
        trial_draft = DeliverableModel(
            deliverable_id="deliv_trial_production",
            hired_instance_id="hired_trial_limits",
            goal_instance_id="goal_trial_limits",
            goal_template_id="daily_post_template",
            title="Trial Production Post",
            payload={
                "platforms": {
                    "instagram": {
                        "caption": "Trial post attempt",
                        "image_url": "https://example.com/trial.jpg",
                    },
                },
            },
            review_status="pending_review",  # Start as pending
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trial_draft)
        db_session.commit()
        
        # Now create approval (deliverable exists now)
        trial_approval = ApprovalModel(
            approval_id="approval_trial",
            deliverable_id="deliv_trial_production",
            customer_id=customer_id,
            decision="approved",
            notes="Approved for testing trial limits",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(trial_approval)
        db_session.commit()
        
        # Update deliverable with approval_id
        trial_draft.review_status = "approved"
        trial_draft.approval_id = "approval_trial"
        db_session.commit()
        
        # Attempt to execute production write (should be blocked)
        with pytest.raises(UsageLimitError) as excinfo:
            enforce_trial_and_budget(
                correlation_id="corr_production_write",
                agent_id=trial_agent.agent_id,
                customer_id=customer_id,
                plan_id=None,
                trial_mode=True,
                intent_action="instagram_create_post",  # Production write action
                effective_estimated_cost_usd=0.5,
                meter_tokens_in=100,
                meter_tokens_out=200,
                purpose="production_write",
                ledger=ledger_new_day,
                events=events_new_day,
                now=now,
            )
        
        error = excinfo.value
        assert error.reason == "trial_production_write_blocked"
        assert "Production write actions are blocked" in str(error)
        assert error.details["intent_action"] == "instagram_create_post"
        
        # Verify draft remains unexecuted
        db_session.refresh(trial_draft)
        assert trial_draft.execution_status == "not_executed"
        
        # ====================================================================
        # Step 7: Upgrade to Paid Subscription
        # ====================================================================
        
        # Convert trial to paid
        trial_agent.trial_status = "ended_converted"
        trial_agent.trial_end_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(trial_agent)
        
        assert trial_agent.trial_status == "ended_converted"
        assert trial_agent.trial_end_at is not None
        
        # ====================================================================
        # Step 8: Production Write Succeeds After Upgrade
        # ====================================================================
        
        # Now trial_mode=False after upgrade
        ledger_paid = InMemoryUsageLedger()
        events_paid = InMemoryUsageEventStore()
        
        # This should succeed (no exception)
        enforce_trial_and_budget(
            correlation_id="corr_paid_production_write",
            agent_id=trial_agent.agent_id,
            customer_id=customer_id,
            plan_id="plan_starter",  # Now on paid plan
            trial_mode=False,  # No longer in trial
            intent_action="instagram_create_post",  # Production write allowed
            effective_estimated_cost_usd=0.5,
            meter_tokens_in=100,
            meter_tokens_out=200,
            purpose="production_write",
            ledger=ledger_paid,
            events=events_paid,
            now=now,
        )
        
        # If we got here, production write is allowed
        
        # Execute the post (mocked)
        with patch("integrations.social.instagram_client.InstagramClient") as mock_instagram:
            mock_instagram_instance = AsyncMock()
            mock_instagram.return_value = mock_instagram_instance
            
            mock_instagram_instance.create_post.return_value = {
                "id": "paid_post_123",
                "permalink": "https://instagram.com/p/paid_test",
            }
            
            post_result = await mock_instagram_instance.create_post(
                caption=trial_draft.payload["platforms"]["instagram"]["caption"],
                image_url=trial_draft.payload["platforms"]["instagram"]["image_url"],
            )
            
            trial_draft.execution_status = "executed"
            trial_draft.executed_at = datetime.now(timezone.utc)
            trial_draft.payload["execution_result"] = {
                "instagram": {
                    "post_id": post_result["id"],
                    "permalink": post_result["permalink"],
                },
            }
            flag_modified(trial_draft, "payload")
            db_session.commit()
            db_session.refresh(trial_draft)
        
        # ====================================================================
        # Step 9: Verify Final State
        # ====================================================================
        
        # Verify agent upgraded
        final_agent = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.hired_instance_id == "hired_trial_limits"
        ).first()
        
        assert final_agent is not None
        assert final_agent.trial_status == "ended_converted"
        assert final_agent.configured is True
        
        # Verify production write executed
        final_draft = db_session.query(DeliverableModel).filter(
            DeliverableModel.deliverable_id == "deliv_trial_production"
        ).first()
        
        assert final_draft is not None
        assert final_draft.execution_status == "executed"
        assert "execution_result" in final_draft.payload
        assert final_draft.payload["execution_result"]["instagram"]["post_id"] == "paid_post_123"
        
        # ====================================================================
        # Step 10: High-Cost Calls Also Allowed After Upgrade
        # ====================================================================
        
        # High-cost operation that was blocked in trial should now succeed
        enforce_trial_and_budget(
            correlation_id="corr_paid_high_cost",
            agent_id=trial_agent.agent_id,
            customer_id=customer_id,
            plan_id="plan_starter",
            trial_mode=False,  # No trial restrictions
            intent_action=None,
            effective_estimated_cost_usd=5.0,  # >$1, but allowed in paid
            meter_tokens_in=10000,
            meter_tokens_out=20000,
            purpose="high_cost_operation",
            ledger=ledger_paid,
            events=events_paid,
            now=now,
        )
        
        # If we got here, high-cost operation is allowed
        assert True
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_trial_not_converted_remains_blocked(self, db_session):
        """Test that trial ended without conversion keeps restrictions.
        
        Verifies trial_status="ended_not_converted" still blocks production writes.
        """
        customer_id = "customer_trial_not_converted"
        ledger = InMemoryUsageLedger()
        events = InMemoryUsageEventStore()
        
        # Create agent with trial ended but not converted
        trial_agent = HiredAgentModel(
            hired_instance_id="hired_trial_not_converted",
            subscription_id="sub_trial_not_converted",
            agent_id="marketing_agent_002",
            customer_id=customer_id,
            nickname="Unconverted Trial Agent",
            theme="professional",
            config={},
            configured=True,
            trial_status="ended_not_converted",  # Trial ended without upgrading
            trial_start_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
            trial_end_at=datetime(2026, 2, 8, tzinfo=timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trial_agent)
        db_session.commit()
        
        # Production writes should still be blocked
        # (In real system, ended_not_converted agents would be deactivated,
        # but for this test we verify metering logic still applies)
        with pytest.raises(UsageLimitError) as excinfo:
            enforce_trial_and_budget(
                correlation_id="corr_not_converted",
                agent_id=trial_agent.agent_id,
                customer_id=customer_id,
                plan_id=None,
                trial_mode=True,  # Still in trial mode (not upgraded)
                intent_action="instagram_create_post",
                effective_estimated_cost_usd=0.5,
                meter_tokens_in=100,
                meter_tokens_out=200,
                purpose="production_write",
                ledger=ledger,
                events=events,
            )
        
        error = excinfo.value
        assert error.reason == "trial_production_write_blocked"
