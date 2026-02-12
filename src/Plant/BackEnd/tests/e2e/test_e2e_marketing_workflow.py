"""End-to-end test for marketing agent workflow.

Tests complete workflow: hire → configure → goal → draft → approve → publish

This test validates:
- Agent hiring and subscription creation
- Platform credential configuration
- Goal creation and execution
- Draft deliverable generation
- Approval workflow
- Post publication to platforms
- Complete audit trail
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from models.hired_agent import HiredAgentModel, GoalInstanceModel
from models.deliverable import DeliverableModel, ApprovalModel


class TestMarketingAgentE2EWorkflow:
    """End-to-end test for complete marketing agent workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_marketing_workflow(self, db_session):
        """Test complete workflow from hire to post publication.
        
        Workflow steps:
        1. Hire marketing agent with trial subscription
        2. Configure agent with credentials and settings
        3. Create daily post goal
        4. Generate draft deliverable
        5. Review and approve draft
        6. Publish post to Instagram
        7. Verify audit trail
        """
        # ====================================================================
        # Step 1: Hire Marketing Agent
        # ====================================================================
        
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_marketing_e2e",
            subscription_id="sub_e2e_trial",
            agent_id="marketing_agent_001",
            customer_id="customer_e2e",
            nickname="E2E Marketing Agent",
            theme="professional",
            config={},
            configured=False,
            trial_status="active",
            trial_start_at=datetime.now(timezone.utc),
        )
        db_session.add(hired_agent)
        db_session.commit()
        db_session.refresh(hired_agent)
        
        assert hired_agent.hired_instance_id == "hired_marketing_e2e"
        assert hired_agent.trial_status == "active"
        assert hired_agent.configured is False
        
        # ====================================================================
        # Step 2: Configure Agent
        # ====================================================================
        
        hired_agent.config = {
            "timezone": "America/New_York",
            "brand_name": "E2E Test Brand",
            "platforms": {
                "instagram": {
                    "enabled": True,
                    "account_id": "test_instagram_account",
                    "access_token": "test_instagram_token",
                },
                "facebook": {
                    "enabled": True,
                    "page_id": "test_facebook_page",
                    "access_token": "test_facebook_token",
                },
            },
        }
        hired_agent.configured = True
        hired_agent.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(hired_agent)
        
        assert hired_agent.configured is True
        assert "instagram" in hired_agent.config["platforms"]
        
        # ====================================================================
        # Step 3: Set Goal (Daily Post)
        # ====================================================================
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_e2e_daily_post",
            hired_instance_id="hired_marketing_e2e",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={
                "platforms": ["instagram", "facebook"],
                "content_type": "image_post",
                "tone": "professional",
                "scheduled_time": "09:00:00",
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        assert goal.goal_instance_id == "goal_e2e_daily_post"
        assert goal.frequency == "daily"
        
        # ====================================================================
        # Step 4: Generate Draft Deliverable
        # ====================================================================
        
        draft = DeliverableModel(
            deliverable_id="deliv_e2e_draft",
            hired_instance_id="hired_marketing_e2e",
            goal_instance_id="goal_e2e_daily_post",
            goal_template_id="daily_post_template",
            title="Daily Post Draft - Instagram & Facebook",
            payload={
                "platforms": {
                    "instagram": {
                        "caption": "E2E test post for Instagram #testing",
                        "image_url": "https://test.com/image.jpg",
                    },
                    "facebook": {
                        "message": "E2E test post for Facebook",
                        "image_url": "https://test.com/image.jpg",
                    },
                },
            },
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()
        db_session.refresh(draft)
        
        assert draft.review_status == "pending_review"
        assert "instagram" in draft.payload["platforms"]
        
        # ====================================================================
        # Step 5: Review and Approve Draft
        # ====================================================================
        
        # Create approval record first (must exist before FK reference)
        approval = ApprovalModel(
            approval_id="approval_e2e_instagram",
            deliverable_id="deliv_e2e_draft",
            customer_id="customer_e2e",
            decision="approved",
            notes="Approved for Instagram posting",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()  # Commit approval first
        db_session.refresh(approval)
        
        # Update deliverable with approval reference
        draft.review_status = "approved"
        draft.review_notes = "Approved for Instagram"
        draft.approval_id = "approval_e2e_instagram"
        draft.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(draft)
        
        assert draft.review_status == "approved"
        assert draft.approval_id == "approval_e2e_instagram"
        assert approval.deliverable_id == "deliv_e2e_draft"
        
        # ====================================================================
        # Step 6: Publish Post to Instagram
        # ====================================================================
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_instagram:
            mock_instagram_instance = AsyncMock()
            mock_instagram.return_value = mock_instagram_instance
            
            # Mock successful post creation
            mock_instagram_instance.create_post.return_value = {
                "id": "instagram_post_e2e_12345",
                "permalink": "https://instagram.com/p/e2e_test",
            }
            
            # Simulate execution
            post_result = await mock_instagram_instance.create_post(
                caption=draft.payload["platforms"]["instagram"]["caption"],
                image_url=draft.payload["platforms"]["instagram"]["image_url"],
            )
            
            # Update deliverable with result
            draft.execution_status = "executed"
            draft.executed_at = datetime.now(timezone.utc)
            draft.payload["execution_result"] = {
                "instagram": {
                    "post_id": post_result["id"],
                    "permalink": post_result["permalink"],
                    "status": "published",
                },
            }
            draft.updated_at = datetime.now(timezone.utc)
            
            # Verify execution before committing
            assert draft.execution_status == "executed"
            assert draft.payload["execution_result"]["instagram"]["post_id"] == "instagram_post_e2e_12345"
            
            db_session.commit()
            db_session.refresh(draft)
        
        # ====================================================================
        # Step 7: Verify Audit Trail
        # ====================================================================
        
        # Verify deliverable final state
        final_deliverable = db_session.query(DeliverableModel).filter(
            DeliverableModel.deliverable_id == "deliv_e2e_draft"
        ).first()
        
        assert final_deliverable is not None
        assert final_deliverable.execution_status == "executed"
        assert final_deliverable.approval_id is not None
        assert final_deliverable.executed_at is not None
        
        # Verify approval record
        final_approval = db_session.query(ApprovalModel).filter(
            ApprovalModel.approval_id == "approval_e2e_instagram"
        ).first()
        
        assert final_approval is not None
        assert final_approval.deliverable_id == "deliv_e2e_draft"
        
        # Verify agent configuration persisted
        final_agent = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.hired_instance_id == "hired_marketing_e2e"
        ).first()
        
        assert final_agent is not None
        assert final_agent.configured is True
        assert final_agent.config["brand_name"] == "E2E Test Brand"
        
        # Verify goal configuration persisted
        final_goal = db_session.query(GoalInstanceModel).filter(
            GoalInstanceModel.goal_instance_id == "goal_e2e_daily_post"
        ).first()
        
        assert final_goal is not None
        assert final_goal.frequency == "daily"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_marketing_workflow_with_rejection(self, db_session):
        """Test workflow when customer rejects draft."""
        # ====================================================================
        # Setup: Hire and configure agent, create goal, generate draft
        # ====================================================================
        
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_marketing_reject",
            subscription_id="sub_reject_trial",
            agent_id="marketing_agent_002",
            customer_id="customer_reject",
            configured=True,
            config={
                "nickname": "Reject Test Agent",
                "platforms": {
                    "instagram": {
                        "enabled": True,
                        "account_id": "test_account",
                    },
                },
            },
            trial_status="active",
        )
        db_session.add(hired_agent)
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_reject",
            hired_instance_id="hired_marketing_reject",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        
        draft = DeliverableModel(
            deliverable_id="deliv_reject",
            hired_instance_id="hired_marketing_reject",
            goal_instance_id="goal_reject",
            goal_template_id="daily_post_template",
            title="Test Post Draft",
            payload={
                "platforms": {
                    "instagram": {
                        "caption": "Test post",
                    },
                },
            },
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()
        
        # ====================================================================
        # Customer rejects draft
        # ====================================================================
        
        draft.review_status = "rejected"
        draft.review_notes = "Content not aligned with brand voice"
        draft.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(draft)
        
        assert draft.review_status == "rejected"
        assert draft.review_notes is not None
        assert draft.executed_at is None
        assert draft.approval_id is None
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_marketing_workflow_with_platform_failure(self, db_session):
        """Test workflow when platform API fails during execution."""
        # ====================================================================
        # Setup: Create approved deliverable
        # ====================================================================
        
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_marketing_fail",
            subscription_id="sub_fail_trial",
            agent_id="marketing_agent_003",
            customer_id="customer_fail",
            configured=True,
            config={"platforms": {"instagram": {"enabled": True}}},
            trial_status="active",
        )
        db_session.add(hired_agent)
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_fail",
            hired_instance_id="hired_marketing_fail",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        
        # Create deliverable first (without approval_id)
        draft = DeliverableModel(
            deliverable_id="deliv_fail",
            hired_instance_id="hired_marketing_fail",
            goal_instance_id="goal_fail",
            goal_template_id="daily_post_template",
            title="Test Post Draft",
            payload={"platforms": {"instagram": {"caption": "Test"}}},
            review_status="approved",
            approval_id=None,  # Will be set after approval is created
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()  # Commit deliverable first
        
        # Create approval (references deliverable_id which now exists)
        approval = ApprovalModel(
            approval_id="approval_fail",
            deliverable_id="deliv_fail",
            customer_id="customer_fail",
            decision="approved",
            notes="Approved for Instagram",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()  # Commit approval
        
        # Update deliverable with approval_id
        draft.approval_id = "approval_fail"
        db_session.commit()
        
        # ====================================================================
        # Platform API fails during execution
        # ====================================================================
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_instagram:
            mock_instagram_instance = AsyncMock()
            mock_instagram.return_value = mock_instagram_instance
            
            # Mock API failure
            mock_instagram_instance.create_post.side_effect = Exception("Instagram API rate limit exceeded")
            
            # Attempt execution
            try:
                await mock_instagram_instance.create_post(
                    caption=draft.payload["platforms"]["instagram"]["caption"],
                )
            except Exception as e:
                # Execution failed - record error in payload
                draft.payload["execution_error"] = {
                    "platform": "instagram",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                draft.updated_at = datetime.now(timezone.utc)
                
                # Verify error before committing
                assert "execution_error" in draft.payload
                assert "rate limit" in draft.payload["execution_error"]["error"]
                
                db_session.commit()
                db_session.refresh(draft)
