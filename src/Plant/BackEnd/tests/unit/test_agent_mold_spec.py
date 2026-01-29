from agent_mold.registry import default_registry
from agent_mold.spec import AgentSpec, DimensionName


def test_agent_spec_normalizes_short_dimension_form():
    spec = AgentSpec(
        agent_id="AGT-MARKETING-001",
        agent_type="marketing",
        dimensions={
            "industry": {"present": False},
        },
    )

    assert DimensionName.INDUSTRY in spec.dimensions
    assert spec.dimensions[DimensionName.INDUSTRY].present is False


def test_compiler_fills_default_null_dimensions():
    spec = AgentSpec(agent_id="AGT-TUTOR-001", agent_type="tutor", dimensions={})
    compiled = default_registry().compile(spec)

    # These are the default optional dimensions in Chunk A.
    assert compiled.dimensions[DimensionName.INDUSTRY].present is False
    assert compiled.dimensions[DimensionName.TEAM].present is False
    assert compiled.dimensions[DimensionName.UI].present is False
    assert compiled.dimensions[DimensionName.LOCALIZATION].present is False


def test_unknown_dimension_is_rejected():
    try:
        AgentSpec(agent_id="AGT-1", agent_type="marketing", dimensions={"unknown": {"present": True}})
        assert False, "Expected ValueError for unknown dimension"
    except ValueError as exc:
        assert "Unknown dimension" in str(exc)
