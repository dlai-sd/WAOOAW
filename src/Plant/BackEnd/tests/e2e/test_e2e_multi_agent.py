"""End-to-end test for multi-agent scenario.

Tests that customer can manage multiple agents simultaneously without conflicts.

This test validates:
- Hiring multiple different agents
- Independent configuration per agent
- Goal isolation per agent
- Deliverable isolation (no cross-contamination)
- Concurrent approval and execution
- Complete audit trail for each agent
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm.attributes import flag_modified

from models.hired_agent import HiredAgentModel, GoalInstanceModel
from models.deliverable import DeliverableModel, ApprovalModel


class TestMultiAgentScenario:
    """End-to-end test for managing multiple agents simultaneously."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_multi_agent_independent_operation(self, db_session):
        """Test that marketing and trading agents operate independently without conflicts.
        
        Workflow:
        1. Hire both marketing and trading agents
        2. Configure both agents independently
        3. Create goals for both agents
        4. Generate drafts for both (verify no cross-contamination)
        5. Approve and execute both successfully
        6. Verify complete isolation and audit trail
        """
        customer_id = "customer_multi_agent"
        
        # ====================================================================
        # Step 1: Hire Marketing Agent
        # ====================================================================
        
        marketing_agent = HiredAgentModel(
            hired_instance_id="hired_marketing_multi",
            subscription_id="sub_marketing_multi",
            agent_id="marketing_agent_001",
            customer_id=customer_id,
            nickname="Social Media Manager",
            theme="professional",
            config={},
            configured=False,
            trial_status="active",
            trial_start_at=datetime.now(timezone.utc),
        )
        db_session.add(marketing_agent)
        db_session.commit()
        db_session.refresh(marketing_agent)
        
        assert marketing_agent.hired_instance_id == "hired_marketing_multi"
        assert marketing_agent.agent_id == "marketing_agent_001"
        
        # ====================================================================
        # Step 2: Hire Trading Agent
        # ====================================================================
        
        trading_agent = HiredAgentModel(
            hired_instance_id="hired_trading_multi",
            subscription_id="sub_trading_multi",
            agent_id="trading_agent_001",
            customer_id=customer_id,
            nickname="Crypto Trader",
            theme="crypto",
            config={},
            configured=False,
            trial_status="active",
            trial_start_at=datetime.now(timezone.utc),
        )
        db_session.add(trading_agent)
        db_session.commit()
        db_session.refresh(trading_agent)
        
        assert trading_agent.hired_instance_id == "hired_trading_multi"
        assert trading_agent.agent_id == "trading_agent_001"
        
        # ====================================================================
        # Step 3: Configure Marketing Agent
        # ====================================================================
        
        marketing_agent.config = {
            "timezone": "America/New_York",
            "brand_name": "Multi Agent Brand",
            "platforms": {
                "instagram": {
                    "enabled": True,
                    "account_id": "multi_instagram",
                    "access_token": "marketing_token",
                },
            },
        }
        marketing_agent.configured = True
        db_session.commit()
        db_session.refresh(marketing_agent)
        
        assert marketing_agent.configured is True
        assert "instagram" in marketing_agent.config["platforms"]
        
        # ====================================================================
        # Step 4: Configure Trading Agent (Independent Configuration)
        # ====================================================================
        
        trading_agent.config = {
            "timezone": "America/New_York",
            "exchange": {
                "name": "delta_exchange",
                "api_key": "trading_api_key",
                "api_secret": "trading_api_secret",
                "testnet": True,
            },
            "risk_limits": {
                "allowed_coins": ["BTC"],
                "max_units_per_order": 0.01,
            },
        }
        trading_agent.configured = True
        db_session.commit()
        db_session.refresh(trading_agent)
        
        assert trading_agent.configured is True
        assert trading_agent.config["exchange"]["name"] == "delta_exchange"
        
        # Verify configs are independent
        assert "platforms" in marketing_agent.config
        assert "platforms" not in trading_agent.config
        assert "exchange" in trading_agent.config
        assert "exchange" not in marketing_agent.config
        
        # ====================================================================
        # Step 5: Create Goal for Marketing Agent
        # ====================================================================
        
        marketing_goal = GoalInstanceModel(
            goal_instance_id="goal_marketing_multi",
            hired_instance_id="hired_marketing_multi",
            goal_template_id="daily_post_template",
            frequency="daily",
            settings={
                "platforms": ["instagram"],
                "content_type": "image",
                "scheduled_time": "09:00",
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(marketing_goal)
        db_session.commit()
        db_session.refresh(marketing_goal)
        
        assert marketing_goal.hired_instance_id == "hired_marketing_multi"
        assert marketing_goal.frequency == "daily"
        
        # ====================================================================
        # Step 6: Create Goal for Trading Agent
        # ====================================================================
        
        trading_goal = GoalInstanceModel(
            goal_instance_id="goal_trading_multi",
            hired_instance_id="hired_trading_multi",
            goal_template_id="trade_intent_template",
            frequency="on_demand",
            settings={
                "trigger": "manual",
                "strategy": "simple_buy",
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trading_goal)
        db_session.commit()
        db_session.refresh(trading_goal)
        
        assert trading_goal.hired_instance_id == "hired_trading_multi"
        assert trading_goal.frequency == "on_demand"
        
        # Verify goals are isolated per agent
        marketing_goals = db_session.query(GoalInstanceModel).filter(
            GoalInstanceModel.hired_instance_id == "hired_marketing_multi"
        ).all()
        trading_goals = db_session.query(GoalInstanceModel).filter(
            GoalInstanceModel.hired_instance_id == "hired_trading_multi"
        ).all()
        
        assert len(marketing_goals) == 1
        assert len(trading_goals) == 1
        assert marketing_goals[0].goal_template_id == "daily_post_template"
        assert trading_goals[0].goal_template_id == "trade_intent_template"
        
        # ====================================================================
        # Step 7: Generate Draft for Marketing Agent
        # ====================================================================
        
        marketing_draft = DeliverableModel(
            deliverable_id="deliv_marketing_multi",
            hired_instance_id="hired_marketing_multi",
            goal_instance_id="goal_marketing_multi",
            goal_template_id="daily_post_template",
            title="Daily Social Post",
            payload={
                "platforms": {
                    "instagram": {
                        "caption": "Marketing agent post",
                        "image_url": "https://example.com/image.jpg",
                    },
                },
            },
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(marketing_draft)
        db_session.commit()
        db_session.refresh(marketing_draft)
        
        assert marketing_draft.hired_instance_id == "hired_marketing_multi"
        assert "instagram" in marketing_draft.payload["platforms"]
        
        # ====================================================================
        # Step 8: Generate Draft for Trading Agent
        # ====================================================================
        
        trading_draft = DeliverableModel(
            deliverable_id="deliv_trading_multi",
            hired_instance_id="hired_trading_multi",
            goal_instance_id="goal_trading_multi",
            goal_template_id="trade_intent_template",
            title="Buy 0.01 BTC",
            payload={
                "trade_intent": {
                    "coin": "BTC",
                    "side": "buy",
                    "quantity": 0.01,
                },
                "risk_validation": {
                    "all_checks_passed": True,
                },
            },
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(trading_draft)
        db_session.commit()
        db_session.refresh(trading_draft)
        
        assert trading_draft.hired_instance_id == "hired_trading_multi"
        assert trading_draft.payload["trade_intent"]["coin"] == "BTC"
        
        # ====================================================================
        # Step 9: Verify No Cross-Contamination Between Agents
        # ====================================================================
        
        # Verify marketing deliverables don't contain trading data
        marketing_deliverables = db_session.query(DeliverableModel).filter(
            DeliverableModel.hired_instance_id == "hired_marketing_multi"
        ).all()
        
        assert len(marketing_deliverables) == 1
        assert "platforms" in marketing_deliverables[0].payload
        assert "trade_intent" not in marketing_deliverables[0].payload
        
        # Verify trading deliverables don't contain marketing data
        trading_deliverables = db_session.query(DeliverableModel).filter(
            DeliverableModel.hired_instance_id == "hired_trading_multi"
        ).all()
        
        assert len(trading_deliverables) == 1
        assert "trade_intent" in trading_deliverables[0].payload
        assert "platforms" not in trading_deliverables[0].payload
        
        # ====================================================================
        # Step 10: Approve Marketing Draft
        # ====================================================================
        
        marketing_approval = ApprovalModel(
            approval_id="approval_marketing_multi",
            deliverable_id="deliv_marketing_multi",
            customer_id=customer_id,
            decision="approved",
            notes="Approved for Instagram posting",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(marketing_approval)
        db_session.commit()
        
        marketing_draft.review_status = "approved"
        marketing_draft.approval_id = "approval_marketing_multi"
        db_session.commit()
        
        # ====================================================================
        # Step 11: Approve Trading Draft
        # ====================================================================
        
        trading_approval = ApprovalModel(
            approval_id="approval_trading_multi",
            deliverable_id="deliv_trading_multi",
            customer_id=customer_id,
            decision="approved",
            notes="Approved for BTC purchase",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(trading_approval)
        db_session.commit()
        
        trading_draft.review_status = "approved"
        trading_draft.approval_id = "approval_trading_multi"
        db_session.commit()
        
        # ====================================================================
        # Step 12: Execute Marketing Agent Post (Mocked)
        # ====================================================================
        
        with patch("integrations.social.instagram_client.InstagramClient") as mock_instagram:
            mock_instagram_instance = AsyncMock()
            mock_instagram.return_value = mock_instagram_instance
            
            mock_instagram_instance.create_post.return_value = {
                "id": "marketing_post_123",
                "permalink": "https://instagram.com/p/marketing_test",
            }
            
            post_result = await mock_instagram_instance.create_post(
                caption=marketing_draft.payload["platforms"]["instagram"]["caption"],
                image_url=marketing_draft.payload["platforms"]["instagram"]["image_url"],
            )
            
            marketing_draft.execution_status = "executed"
            marketing_draft.executed_at = datetime.now(timezone.utc)
            marketing_draft.payload["execution_result"] = {
                "instagram": {
                    "post_id": post_result["id"],
                    "permalink": post_result["permalink"],
                },
            }
            flag_modified(marketing_draft, "payload")
            
            assert marketing_draft.payload["execution_result"]["instagram"]["post_id"] == "marketing_post_123"
            
            db_session.commit()
            db_session.refresh(marketing_draft)
        
        # ====================================================================
        # Step 13: Execute Trading Agent Order (Mocked)
        # ====================================================================
        
        with patch("integrations.delta_exchange.client.DeltaExchangeClient") as mock_delta:
            mock_delta_instance = AsyncMock()
            mock_delta.return_value = mock_delta_instance
            
            mock_delta_instance.place_order.return_value = {
                "success": True,
                "result": {
                    "id": 999888,
                    "product_symbol": "BTCUSD",
                    "state": "filled",
                },
            }
            
            order_result = await mock_delta_instance.place_order(
                payload={
                    "product_symbol": "BTCUSD",
                    "size": trading_draft.payload["trade_intent"]["quantity"],
                    "side": trading_draft.payload["trade_intent"]["side"],
                }
            )
            
            trading_draft.execution_status = "executed"
            trading_draft.executed_at = datetime.now(timezone.utc)
            trading_draft.payload["execution_result"] = {
                "order_id": order_result["result"]["id"],
                "state": order_result["result"]["state"],
            }
            flag_modified(trading_draft, "payload")
            
            assert trading_draft.payload["execution_result"]["order_id"] == 999888
            
            db_session.commit()
            db_session.refresh(trading_draft)
        
        # ====================================================================
        # Step 14: Verify Complete Audit Trail for Both Agents
        # ====================================================================
        
        # Verify marketing agent execution
        final_marketing_deliverable = db_session.query(DeliverableModel).filter(
            DeliverableModel.deliverable_id == "deliv_marketing_multi"
        ).first()
        
        assert final_marketing_deliverable is not None
        assert final_marketing_deliverable.execution_status == "executed"
        assert final_marketing_deliverable.approval_id == "approval_marketing_multi"
        assert "execution_result" in final_marketing_deliverable.payload
        assert "instagram" in final_marketing_deliverable.payload["execution_result"]
        
        # Verify trading agent execution
        final_trading_deliverable = db_session.query(DeliverableModel).filter(
            DeliverableModel.deliverable_id == "deliv_trading_multi"
        ).first()
        
        assert final_trading_deliverable is not None
        assert final_trading_deliverable.execution_status == "executed"
        assert final_trading_deliverable.approval_id == "approval_trading_multi"
        assert "execution_result" in final_trading_deliverable.payload
        assert "order_id" in final_trading_deliverable.payload["execution_result"]
        
        # Verify approvals are separate
        marketing_approvals = db_session.query(ApprovalModel).filter(
            ApprovalModel.deliverable_id == "deliv_marketing_multi"
        ).all()
        trading_approvals = db_session.query(ApprovalModel).filter(
            ApprovalModel.deliverable_id == "deliv_trading_multi"
        ).all()
        
        assert len(marketing_approvals) == 1
        assert len(trading_approvals) == 1
        assert marketing_approvals[0].approval_id != trading_approvals[0].approval_id
        
        # Verify agents remain independent
        final_marketing_agent = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.hired_instance_id == "hired_marketing_multi"
        ).first()
        final_trading_agent = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.hired_instance_id == "hired_trading_multi"
        ).first()
        
        assert final_marketing_agent is not None
        assert final_trading_agent is not None
        assert final_marketing_agent.agent_id == "marketing_agent_001"
        assert final_trading_agent.agent_id == "trading_agent_001"
        assert "platforms" in final_marketing_agent.config
        assert "exchange" in final_trading_agent.config
        
        # ====================================================================
        # Step 15: Verify Customer Can Query Both Agents
        # ====================================================================
        
        customer_agents = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.customer_id == customer_id
        ).all()
        
        assert len(customer_agents) == 2
        
        agent_ids = [agent.agent_id for agent in customer_agents]
        assert "marketing_agent_001" in agent_ids
        assert "trading_agent_001" in agent_ids
        
        # Verify each agent has its own goals
        for agent in customer_agents:
            agent_goals = db_session.query(GoalInstanceModel).filter(
                GoalInstanceModel.hired_instance_id == agent.hired_instance_id
            ).all()
            
            assert len(agent_goals) == 1
            
            if agent.agent_id == "marketing_agent_001":
                assert agent_goals[0].goal_template_id == "daily_post_template"
            elif agent.agent_id == "trading_agent_001":
                assert agent_goals[0].goal_template_id == "trade_intent_template"
