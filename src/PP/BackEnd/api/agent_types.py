"""Agent type definition management (PP).

Phase 1: PP provides an admin UI to edit/publish AgentTypeDefinitions.

Implementation notes:
- PP validates the schema payload and forwards it to Plant, which is the
  authoritative store.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, model_validator

from api.deps import get_authorization_header
from api.security import require_admin
from clients.plant_client import PlantAPIClient, get_plant_client, PlantAPIError, ValidationError


FieldType = Literal["text", "enum", "list", "object", "boolean", "number"]


class SchemaFieldDefinition(BaseModel):
    key: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    type: FieldType
    required: bool = False
    description: Optional[str] = None

    options: Optional[list[str]] = None
    item_type: Optional[FieldType] = None

    @model_validator(mode="after")
    def _validate_constraints(self):
        if self.type == "enum":
            if not self.options:
                raise ValueError("enum fields require options")
        if self.type == "list":
            if not self.item_type:
                raise ValueError("list fields require item_type")
        return self


class JsonSchemaDefinition(BaseModel):
    fields: list[SchemaFieldDefinition] = Field(default_factory=list)


class GoalTemplateDefinition(BaseModel):
    goal_template_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    default_frequency: str = Field(..., min_length=1)
    settings_schema: JsonSchemaDefinition = Field(default_factory=JsonSchemaDefinition)
    skill_binding: Optional[str] = None


class EnforcementDefaults(BaseModel):
    approval_required: bool = True
    deterministic: bool = False


class AgentTypeDefinition(BaseModel):
    agent_type_id: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    required_skill_keys: list[str] = Field(default_factory=list)
    config_schema: JsonSchemaDefinition = Field(default_factory=JsonSchemaDefinition)
    goal_templates: list[GoalTemplateDefinition] = Field(default_factory=list)
    enforcement_defaults: EnforcementDefaults = Field(default_factory=EnforcementDefaults)


router = APIRouter(prefix="/agent-types", tags=["agent-types"])


def _correlation_id_from_request(request: Request) -> Optional[str]:
    return request.headers.get("x-correlation-id") or request.headers.get("X-Correlation-ID")


@router.get("", response_model=list[dict[str, Any]])
async def list_agent_types(
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> list[dict[str, Any]]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.list_agent_type_definitions(
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{agent_type_id}", response_model=dict[str, Any])
async def get_agent_type(
    agent_type_id: str,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> dict[str, Any]:
    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.get_agent_type_definition(
            agent_type_id,
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/{agent_type_id}", response_model=dict[str, Any])
async def publish_agent_type(
    agent_type_id: str,
    body: AgentTypeDefinition,
    request: Request,
    auth_header: Optional[str] = Depends(get_authorization_header),
    _: dict = Depends(require_admin),
    plant_client: PlantAPIClient = Depends(get_plant_client),
) -> dict[str, Any]:
    if (body.agent_type_id or "").strip() != (agent_type_id or "").strip():
        raise HTTPException(status_code=400, detail="agent_type_id mismatch")

    correlation_id = _correlation_id_from_request(request)
    try:
        return await plant_client.upsert_agent_type_definition(
            agent_type_id,
            body.model_dump(mode="json"),
            correlation_id=correlation_id,
            auth_header=auth_header,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PlantAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))
