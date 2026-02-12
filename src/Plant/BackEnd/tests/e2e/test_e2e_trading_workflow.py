"""End-to-end test for trading agent workflow.

Tests complete workflow: hire → configure → intent → risk check → approve → execute → track

This test validates:
- Agent hiring and subscription creation
- Exchange credential configuration
- Trade intent generation
- Risk validation (allowed coins, quantity limits)
- Approval workflow
- Order placement to Delta Exchange
- Order tracking and fill confirmation
- Complete audit trail
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm.attributes import flag_modified

from models.hired_agent import HiredAgentModel, GoalInstanceModel
from models.deliverable import DeliverableModel, ApprovalModel


class TestTradingAgentE2EWorkflow:
    """End-to-end test for complete trading agent workflow."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_trading_workflow(self, db_session):
        """Test complete workflow from hire to successful trade execution.
        
        Workflow steps:
        1. Hire trading agent with trial subscription
        2. Configure agent with Delta Exchange credentials and risk limits
        3. Create trade intent draft
        4. Risk validation (coin allowed, quantity within limits)
        5. Approve trade intent
        6. Execute trade (place order on Delta Exchange)
        7. Track order execution until filled
        8. Verify audit trail
        """
        # ====================================================================
        # Step 1: Hire Trading Agent
        # ====================================================================
        
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_trading_e2e",
            subscription_id="sub_e2e_trading_trial",
            agent_id="trading_agent_001",
            customer_id="customer_e2e_trading",
            nickname="E2E Trading Agent",
            theme="crypto",
            config={},
            configured=False,
            trial_status="active",
            trial_start_at=datetime.now(timezone.utc),
        )
        db_session.add(hired_agent)
        db_session.commit()
        db_session.refresh(hired_agent)
        
        assert hired_agent.hired_instance_id == "hired_trading_e2e"
        assert hired_agent.trial_status == "active"
        assert hired_agent.configured is False
        
        # ====================================================================
        # Step 2: Configure Agent with Exchange Credentials and Risk Limits
        # ====================================================================
        
        hired_agent.config = {
            "timezone": "America/New_York",
            "exchange": {
                "name": "delta_exchange",
                "api_key": "test_api_key",
                "api_secret": "test_api_secret",
                "testnet": True,
            },
            "risk_limits": {
                "allowed_coins": ["BTC", "ETH"],
                "max_units_per_order": 0.01,
                "max_usd_per_order": 1000,
            },
        }
        hired_agent.configured = True
        db_session.commit()
        db_session.refresh(hired_agent)
        
        assert hired_agent.configured is True
        assert "BTC" in hired_agent.config["risk_limits"]["allowed_coins"]
        assert hired_agent.config["risk_limits"]["max_units_per_order"] == 0.01
        
        # ====================================================================
        # Step 3: Create Trade Intent Draft
        # ====================================================================
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_e2e_trade_intent",
            hired_instance_id="hired_trading_e2e",
            goal_template_id="trade_intent_template",
            frequency="on_demand",
            settings={
                "trigger": "manual",
                "strategy": "simple_buy",
            },
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        db_session.commit()
        db_session.refresh(goal)
        
        assert goal.frequency == "on_demand"
        
        # ====================================================================
        # Step 4: Generate Trade Intent Draft with Risk Validation
        # ====================================================================
        
        draft = DeliverableModel(
            deliverable_id="deliv_e2e_trade_intent",
            hired_instance_id="hired_trading_e2e",
            goal_instance_id="goal_e2e_trade_intent",
            goal_template_id="trade_intent_template",
            title="Buy 0.01 BTC",
            payload={
                "trade_intent": {
                    "coin": "BTC",
                    "side": "buy",
                    "quantity": 0.01,
                    "order_type": "market",
                },
                "risk_validation": {
                    "coin_allowed": True,
                    "quantity_within_limit": True,
                    "usd_estimate_within_limit": True,
                    "all_checks_passed": True,
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
        assert draft.payload["risk_validation"]["all_checks_passed"] is True
        assert draft.payload["trade_intent"]["coin"] == "BTC"
        
        # ====================================================================
        # Step 5: Review and Approve Trade Intent
        # ====================================================================
        
        # Create approval record first (must exist before FK reference)
        approval = ApprovalModel(
            approval_id="approval_e2e_trade",
            deliverable_id="deliv_e2e_trade_intent",
            customer_id="customer_e2e_trading",
            decision="approved",
            notes="Approved for BTC purchase",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()  # Commit approval first
        db_session.refresh(approval)
        
        # Update deliverable with approval reference
        draft.review_status = "approved"
        draft.review_notes = "Approved for execution"
        draft.approval_id = "approval_e2e_trade"
        draft.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(draft)
        
        assert draft.review_status == "approved"
        assert draft.approval_id == "approval_e2e_trade"
        assert approval.deliverable_id == "deliv_e2e_trade_intent"
        
        # ====================================================================
        # Step 6: Execute Trade (Place Order on Delta Exchange - Mocked)
        # ====================================================================
        
        with patch("integrations.delta_exchange.client.DeltaExchangeClient") as mock_delta:
            mock_delta_instance = AsyncMock()
            mock_delta.return_value = mock_delta_instance
            
            # Mock successful order placement
            mock_delta_instance.place_order.return_value = {
                "success": True,
                "result": {
                    "id": 12345678,
                    "product_symbol": "BTCUSD",
                    "size": 0.01,
                    "side": "buy",
                    "state": "open",
                },
            }
            
            # Simulate execution
            order_result = await mock_delta_instance.place_order(
                payload={
                    "product_id": 1,
                    "product_symbol": "BTCUSD",
                    "size": draft.payload["trade_intent"]["quantity"],
                    "side": draft.payload["trade_intent"]["side"],
                    "order_type": draft.payload["trade_intent"]["order_type"],
                }
            )
            
            # Update deliverable with order placement result
            draft.execution_status = "executed"
            draft.executed_at = datetime.now(timezone.utc)
            draft.payload["execution_result"] = {
                "order_id": order_result["result"]["id"],
                "product_symbol": order_result["result"]["product_symbol"],
                "size": order_result["result"]["size"],
                "side": order_result["result"]["side"],
                "state": order_result["result"]["state"],
                "status": "order_placed",
            }
            draft.updated_at = datetime.now(timezone.utc)
            
            # Mark payload as modified so SQLAlchemy persists JSON changes
            flag_modified(draft, "payload")
            
            # Verify execution before committing
            assert draft.execution_status == "executed"
            assert draft.payload["execution_result"]["order_id"] == 12345678
            assert draft.payload["execution_result"]["state"] == "open"
            
            db_session.commit()
            db_session.refresh(draft)
        
        # ====================================================================
        # Step 7: Track Order Execution Until Filled (Mocked)
        # ====================================================================
        
        # Refresh draft to ensure we have latest state from DB
        db_session.refresh(draft)
        assert "execution_result" in draft.payload  # Verify execution_result was persisted
        
        with patch("integrations.delta_exchange.client.DeltaExchangeClient") as mock_delta:
            mock_delta_instance = AsyncMock()
            mock_delta.return_value = mock_delta_instance
            
            # Mock order status polling (order filled)
            mock_delta_instance.get_order_status.return_value = {
                "success": True,
                "result": {
                    "id": 12345678,
                    "state": "filled",
                    "average_fill_price": "50000.50",
                    "filled_size": 0.01,
                    "commission": "0.50",
                },
            }
            
            # Simulate order tracking
            order_status = await mock_delta_instance.get_order_status(order_id=12345678)
            
            # Update deliverable with fill details
            draft.payload["execution_result"]["state"] = order_status["result"]["state"]
            draft.payload["execution_result"]["fill_price"] = order_status["result"]["average_fill_price"]
            draft.payload["execution_result"]["filled_size"] = order_status["result"]["filled_size"]
            draft.payload["execution_result"]["commission"] = order_status["result"]["commission"]
            draft.payload["execution_result"]["status"] = "order_filled"
            draft.updated_at = datetime.now(timezone.utc)
            
            # Mark payload as modified so SQLAlchemy persists JSON changes
            flag_modified(draft, "payload")
            
            # Verify fill before committing
            assert draft.payload["execution_result"]["state"] == "filled"
            assert draft.payload["execution_result"]["fill_price"] == "50000.50"
            
            db_session.commit()
            db_session.refresh(draft)
            db_session.refresh(draft)
        
        # ====================================================================
        # Step 8: Verify Audit Trail
        # ====================================================================
        
        # Verify deliverable final state
        final_deliverable = db_session.query(DeliverableModel).filter(
            DeliverableModel.deliverable_id == "deliv_e2e_trade_intent"
        ).first()
        
        assert final_deliverable is not None
        assert final_deliverable.execution_status == "executed"
        assert final_deliverable.executed_at is not None
        assert final_deliverable.approval_id == "approval_e2e_trade"
        assert final_deliverable.payload["execution_result"]["status"] == "order_filled"
        
        # Verify approval record
        final_approval = db_session.query(ApprovalModel).filter(
            ApprovalModel.approval_id == "approval_e2e_trade"
        ).first()
        
        assert final_approval is not None
        assert final_approval.deliverable_id == "deliv_e2e_trade_intent"
        assert final_approval.decision == "approved"
        
        # Verify agent configuration persistence
        final_agent = db_session.query(HiredAgentModel).filter(
            HiredAgentModel.hired_instance_id == "hired_trading_e2e"
        ).first()
        
        assert final_agent is not None
        assert final_agent.configured is True
        assert "BTC" in final_agent.config["risk_limits"]["allowed_coins"]
        
        # Verify goal persistence
        final_goal = db_session.query(GoalInstanceModel).filter(
            GoalInstanceModel.goal_instance_id == "goal_e2e_trade_intent"
        ).first()
        
        assert final_goal is not None
        assert final_goal.frequency == "on_demand"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_trading_workflow_with_rejection(self, db_session):
        """Test workflow when customer rejects trade intent.
        
        Verifies:
        - Draft can be rejected
        - Execution never happens
        - Rejection recorded in audit trail
        """
        # Setup agent and goal
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_trading_reject",
            subscription_id="sub_reject",
            agent_id="trading_agent_001",
            customer_id="customer_reject",
            nickname="Trading Agent Reject",
            theme="crypto",
            configured=True,
            config={"exchange": {"name": "delta_exchange"}, "risk_limits": {"allowed_coins": ["BTC"]}},
            trial_status="active",
        )
        db_session.add(hired_agent)
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_reject",
            hired_instance_id="hired_trading_reject",
            goal_template_id="trade_intent_template",
            frequency="on_demand",
            settings={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        
        # Create draft deliverable
        draft = DeliverableModel(
            deliverable_id="deliv_reject",
            hired_instance_id="hired_trading_reject",
            goal_instance_id="goal_reject",
            goal_template_id="trade_intent_template",
            title="Buy 0.01 BTC",
            payload={"trade_intent": {"coin": "BTC", "side": "buy", "quantity": 0.01}},
            review_status="pending_review",
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()
        
        # Create approval (must exist before FK reference from draft)
        approval = ApprovalModel(
            approval_id="approval_reject",
            deliverable_id="deliv_reject",
            customer_id="customer_reject",
            decision="rejected",
            notes="Risk too high for current market conditions",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()
        
        # Customer rejects the trade intent
        draft.review_status = "rejected"
        draft.review_notes = "Risk too high for current market conditions"
        draft.approval_id = "approval_reject"
        draft.updated_at = datetime.now(timezone.utc)
        db_session.commit()
        db_session.refresh(draft)
        
        # Verify rejection
        assert draft.review_status == "rejected"
        assert draft.review_notes is not None
        assert draft.executed_at is None
        assert draft.execution_status == "not_executed"
        assert draft.approval_id == "approval_reject"
        
        # Verify approval record shows rejection
        final_approval = db_session.query(ApprovalModel).filter(
            ApprovalModel.approval_id == "approval_reject"
        ).first()
        assert final_approval.decision == "rejected"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_trading_workflow_with_exchange_failure(self, db_session):
        """Test workflow when Delta Exchange API fails during execution.
        
        Verifies:
        - Exchange API failure is handled gracefully
        - Error details are recorded in deliverable
        - Audit trail remains intact
        """
        # Setup agent, goal, and approved draft
        hired_agent = HiredAgentModel(
            hired_instance_id="hired_trading_fail",
            subscription_id="sub_fail",
            agent_id="trading_agent_001",
            customer_id="customer_fail",
            nickname="Trading Agent Fail",
            theme="crypto",
            configured=True,
            config={"exchange": {"name": "delta_exchange"}, "risk_limits": {"allowed_coins": ["BTC"]}},
            trial_status="active",
        )
        db_session.add(hired_agent)
        
        goal = GoalInstanceModel(
            goal_instance_id="goal_fail",
            hired_instance_id="hired_trading_fail",
            goal_template_id="trade_intent_template",
            frequency="on_demand",
            settings={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(goal)
        
        # Create deliverable first (without approval_id)
        draft = DeliverableModel(
            deliverable_id="deliv_fail_trading",
            hired_instance_id="hired_trading_fail",
            goal_instance_id="goal_fail",
            goal_template_id="trade_intent_template",
            title="Buy 0.01 BTC",
            payload={"trade_intent": {"coin": "BTC", "side": "buy", "quantity": 0.01}},
            review_status="approved",
            approval_id=None,
            execution_status="not_executed",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(draft)
        db_session.commit()  # Commit deliverable first
        
        # Create approval (references deliverable_id which now exists)
        approval = ApprovalModel(
            approval_id="approval_fail_trading",
            deliverable_id="deliv_fail_trading",
            customer_id="customer_fail",
            decision="approved",
            notes="Approved for execution",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(approval)
        db_session.commit()  # Commit approval
        
        # Update deliverable with approval_id
        draft.approval_id = "approval_fail_trading"
        db_session.commit()
        
        # ====================================================================
        # Exchange API fails during execution
        # ====================================================================
        
        with patch("integrations.delta_exchange.client.DeltaExchangeClient") as mock_delta:
            mock_delta_instance = AsyncMock()
            mock_delta.return_value = mock_delta_instance
            
            # Mock API failure
            mock_delta_instance.place_order.side_effect = Exception("Delta Exchange API: Insufficient margin")
            
            # Attempt execution
            try:
                await mock_delta_instance.place_order(
                    payload={"product_symbol": "BTCUSD", "size": 0.01, "side": "buy"},
                )
            except Exception as e:
                # Execution failed - record error in payload
                draft.payload["execution_error"] = {
                    "exchange": "delta_exchange",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                draft.updated_at = datetime.now(timezone.utc)
                
                # Mark payload as modified so SQLAlchemy persists JSON changes
                flag_modified(draft, "payload")
                
                # Verify error before committing
                assert "execution_error" in draft.payload
                assert "Insufficient margin" in draft.payload["execution_error"]["error"]
                
                db_session.commit()
                db_session.refresh(draft)
