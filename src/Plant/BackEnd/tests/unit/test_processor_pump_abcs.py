"""Unit tests for BaseProcessor + BasePump ABCs (PLANT-MOULD-1 E1-S1)."""
import asyncio

import pytest

from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput
from agent_mold.pump import BasePump, GoalConfigPump
from agent_mold.skills.content_creator import ContentCreatorSkill
from agent_mold.skills.trading_executor import TradingExecutor


def test_content_creator_is_base_processor():
    assert issubclass(ContentCreatorSkill, BaseProcessor)


def test_trading_executor_is_base_processor():
    assert issubclass(TradingExecutor, BaseProcessor)


def test_goal_config_pump_is_base_pump():
    assert issubclass(GoalConfigPump, BasePump)


def test_base_processor_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseProcessor()  # type: ignore


def test_base_pump_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BasePump()  # type: ignore


def test_processor_input_fields():
    inp = ProcessorInput(
        goal_config={"k": "v"},
        raw_data={"d": 1},
        correlation_id="cid-1",
        hired_agent_id="ha-1",
    )
    assert inp.goal_config == {"k": "v"}
    assert inp.hired_agent_id == "ha-1"


def test_goal_config_pump_returns_goal_config():
    pump = GoalConfigPump()
    cfg = {"x": 1}
    result = asyncio.get_event_loop().run_until_complete(
        pump.pull(goal_config=cfg, hired_agent_id="ha-1")
    )
    assert result == cfg


def test_processor_output_fields():
    out = ProcessorOutput(result="ok", metadata={"k": "v"}, correlation_id="cid-1")
    assert out.result == "ok"
    assert out.correlation_id == "cid-1"


def test_processor_type_returns_class_name():
    assert ContentCreatorSkill.processor_type() == "ContentCreatorSkill"
    assert TradingExecutor.processor_type() == "TradingExecutor"


def test_pump_type_returns_class_name():
    assert GoalConfigPump.pump_type() == "GoalConfigPump"
