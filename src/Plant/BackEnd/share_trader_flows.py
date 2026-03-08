"""Share Trader flow definitions (EXEC-ENGINE-001 E6-S1).

Two flows wire the three Share Trader components:

  MarketAnalysisFlow  — DeltaExchangePump → RSIProcessor (no approval gate)
  ExecuteTradeFlow    — DeltaPublisher alone (approval gate at step 0 so
                        customers review the RSI signal before execution)

FLOW_REGISTRY maps flow_name → flow_def dict. The flow-runs endpoint uses this
to look up any registered flow by name without hard-coding flow logic.
"""
from __future__ import annotations

MARKET_ANALYSIS_FLOW: dict = {
    "flow_name": "MarketAnalysisFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaExchangePump"},
        {"step_name": "step_2", "component_type": "RSIProcessor"},
    ],
    "approval_gate_index": None,
}

EXECUTE_TRADE_FLOW: dict = {
    "flow_name": "ExecuteTradeFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaPublisher"},
    ],
    "approval_gate_index": 0,  # Gate fires before DeltaPublisher
}

FLOW_REGISTRY: dict[str, dict] = {
    "MarketAnalysisFlow": MARKET_ANALYSIS_FLOW,
    "ExecuteTradeFlow": EXECUTE_TRADE_FLOW,
}
