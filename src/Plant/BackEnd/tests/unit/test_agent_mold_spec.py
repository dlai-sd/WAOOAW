import hashlib
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.agent_mold import router as agent_mold_router

from agent_mold.registry import default_registry
from agent_mold.spec import AgentSpec, DimensionName
from agent_mold.reference_agents import REFERENCE_AGENTS


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

    # Default null dimensions include everything except SKILL.
    assert compiled.dimensions[DimensionName.INDUSTRY].present is False
    assert compiled.dimensions[DimensionName.TEAM].present is False
    assert compiled.dimensions[DimensionName.UI].present is False
    assert compiled.dimensions[DimensionName.LOCALIZATION].present is False
    assert compiled.dimensions[DimensionName.INTEGRATIONS].present is False
    assert compiled.dimensions[DimensionName.TRIAL].present is False
    assert compiled.dimensions[DimensionName.BUDGET].present is False


def test_unknown_dimension_is_rejected():
    try:
        AgentSpec(agent_id="AGT-1", agent_type="marketing", dimensions={"unknown": {"present": True}})
        assert False, "Expected ValueError for unknown dimension"
    except ValueError as exc:
        assert "Unknown dimension" in str(exc)


def test_present_skill_requires_category_and_primary_identifier():
    try:
        AgentSpec(
            agent_id="AGT-1",
            agent_type="marketing",
            dimensions={
                "skill": {"present": True, "config": {"primary_playbook_id": "X"}},
            },
        )
        assert False, "Expected ValueError for missing category"
    except ValueError as exc:
        assert "missing required config keys" in str(exc) or "category" in str(exc)

    try:
        AgentSpec(
            agent_id="AGT-2",
            agent_type="marketing",
            dimensions={
                "skill": {"present": True, "config": {"category": "marketing"}},
            },
        )
        assert False, "Expected ValueError for missing primary identifier"
    except ValueError as exc:
        assert "primary identifier" in str(exc)


def test_null_dimension_must_not_include_config():
    try:
        AgentSpec(
            agent_id="AGT-3",
            agent_type="marketing",
            dimensions={
                "industry": {"present": False, "config": {"industry": "beauty"}},
            },
        )
        assert False, "Expected ValueError for null dimension with config"
    except ValueError as exc:
        assert "must not include config" in str(exc)


def test_unsupported_dimension_version_is_rejected():
    try:
        AgentSpec(
            agent_id="AGT-4",
            agent_type="marketing",
            dimensions={
                "skill": {
                    "present": True,
                    "version": "9.9",
                    "config": {"category": "marketing", "primary_playbook_id": "X"},
                },
            },
        )
        assert False, "Expected ValueError for unsupported version"
    except ValueError as exc:
        assert "Unsupported version" in str(exc)


def test_agent_spec_schema_endpoint_is_stable_snapshot():
    # Unit-test-only app: avoid `main.py` startup DB initialization.
    app = FastAPI()
    app.include_router(agent_mold_router, prefix="/api/v1")

    with TestClient(app) as client:
        resp = client.get("/api/v1/agent-mold/schema/agent-spec")
        assert resp.status_code == 200
        schema = resp.json()

    assert schema.get("title") == "AgentSpec"
    assert schema.get("type") == "object"

    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # Snapshot hash: update intentionally when schema changes.
    assert digest == "5373c8829ee7a68fb30a63ad70e05a460de3f7815e676e879f88dc15a011514c"


def test_validate_endpoint_returns_422_for_invalid_spec():
    app = FastAPI()
    app.include_router(agent_mold_router, prefix="/api/v1")

    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/agent-mold/spec/validate",
            json={
                "agent_id": "AGT-INVALID",
                "agent_type": "marketing",
                "dimensions": {
                    "skill": {"present": True, "config": {"category": "marketing"}},
                },
            },
        )

    assert resp.status_code == 422
    payload = resp.json()
    assert "detail" in payload


def test_reference_agents_compile_and_materialize_runtime_bundle():
    registry = default_registry()

    for ref in REFERENCE_AGENTS:
        compiled = registry.compile(ref.spec)
        bundle = registry.materialize(compiled)

        assert bundle.compiled.agent_id == ref.agent_id

        # Present dimensions in reference specs should materialize as present.
        assert bundle.artifacts[DimensionName.SKILL]["present"] is True
        assert bundle.artifacts[DimensionName.INDUSTRY]["present"] is True
        assert bundle.artifacts[DimensionName.TRIAL]["present"] is True
        assert bundle.artifacts[DimensionName.BUDGET]["present"] is True

        # Optional dims should still exist (explicit nulls).
        assert DimensionName.INTEGRATIONS in bundle.artifacts
