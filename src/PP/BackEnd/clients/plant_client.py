"""
Plant API Client for Platform Portal
Type-safe Python client with retry logic, error handling, and correlation ID support
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings


class PlantAPIError(Exception):
    """Base exception for Plant API errors"""
    pass


class ConstitutionalAlignmentError(PlantAPIError):
    """Constitutional alignment violation (L0/L1)"""
    pass


class EntityNotFoundError(PlantAPIError):
    """Entity not found in Plant"""
    pass


class DuplicateEntityError(PlantAPIError):
    """Duplicate entity (409 Conflict)"""
    pass


class ValidationError(PlantAPIError):
    """Request validation error (422)"""
    pass


# Pydantic models (copied from Plant schemas for type safety)
class SkillCreate:
    """Create skill request schema"""
    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        skill_key: Optional[str] = None,
        governance_agent_id: str = "genesis",
    ):
        self.name = name
        self.description = description
        self.category = category
        self.skill_key = skill_key
        self.governance_agent_id = governance_agent_id
    
    def dict(self):
        data = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "governance_agent_id": self.governance_agent_id
        }
        if self.skill_key is not None:
            data["skill_key"] = self.skill_key
        return data


class SkillResponse:
    """Skill response schema"""
    def __init__(self, data: dict):
        self.id = data["id"]
        self.external_id = data.get("external_id")
        self.name = data["name"]
        self.description = data["description"]
        self.category = data["category"]
        self.entity_type = data.get("entity_type", "skill")
        self.status = data.get("status", "pending_certification")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.l0_compliance_status = data.get("l0_compliance_status", {})


class JobRoleCreate:
    """Create job role request schema"""
    def __init__(self, name: str, description: str, required_skills: List[str], 
                 seniority_level: str = "mid", governance_agent_id: str = "genesis"):
        self.name = name
        self.description = description
        self.required_skills = required_skills
        self.seniority_level = seniority_level
        self.governance_agent_id = governance_agent_id
    
    def dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "required_skills": self.required_skills,
            "seniority_level": self.seniority_level,
            "governance_agent_id": self.governance_agent_id
        }


class JobRoleResponse:
    """Job role response schema"""
    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data["name"]
        self.description = data["description"]
        self.required_skills = data.get("required_skills", [])
        self.seniority_level = data.get("seniority_level", "mid")
        self.entity_type = data.get("entity_type", "job_role")
        self.status = data.get("status", "pending_certification")
        self.created_at = data.get("created_at")


class AgentCreate:
    """Create agent request schema.

    Note: PP routes currently use fields like `description` and `industry` (string)
    rather than Plant's older `industry_id` model. This class supports both.
    """

    def __init__(
        self,
        name: str,
        job_role_id: str,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        team_id: Optional[str] = None,
        governance_agent_id: str = "genesis",
        # Backward-compatible fields (optional)
        skill_id: Optional[str] = None,
        industry_id: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.job_role_id = job_role_id
        self.industry = industry or industry_id
        self.team_id = team_id
        self.governance_agent_id = governance_agent_id
        self.skill_id = skill_id

    def dict(self):
        data: Dict[str, Any] = {
            "name": self.name,
            "job_role_id": self.job_role_id,
            "governance_agent_id": self.governance_agent_id,
        }
        if self.description is not None:
            data["description"] = self.description
        if self.industry is not None:
            # Prefer the modern `industry` key; Plant can normalize as needed.
            data["industry"] = self.industry
        if self.skill_id is not None:
            data["skill_id"] = self.skill_id
        if self.team_id:
            data["team_id"] = self.team_id
        return data


class AgentResponse:
    """Agent response schema."""

    def __init__(self, data: dict):
        self.id = data["id"]
        self.name = data.get("name")
        self.description = data.get("description")
        self.job_role_id = data.get("job_role_id")
        # Support both `industry` and legacy `industry_id`.
        self.industry = data.get("industry") or data.get("industry_id")
        self.industry_id = data.get("industry_id")
        self.skill_id = data.get("skill_id")
        self.team_id = data.get("team_id")
        self.team_name = data.get("team_name")
        self.status = data.get("status", "active")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")


class ErrorResponse:
    """RFC 7807 error response schema"""
    def __init__(self, data: dict):
        self.type = data.get("type", "")
        self.title = data.get("title", "")
        self.status = data.get("status", 500)
        self.detail = data.get("detail", "")
        self.instance = data.get("instance", "")
        self.correlation_id = data.get("correlation_id")
        self.violations = data.get("violations", [])


class PlantAPIClient:
    """
    Async HTTP client for Plant API with retry logic and error handling.
    
    Features:
    - Automatic retry with exponential backoff (3 attempts, max 10s delay)
    - Correlation ID propagation for request tracing
    - Type-safe request/response models
    - RFC 7807 error parsing
    - Timeout configuration (30s default)
    
    Example:
        client = PlantAPIClient()
        skill = await client.create_skill(SkillCreate(
            name="Python 3.11",
            description="Modern Python programming",
            category="technical"
        ))
        print(f"Created skill: {skill.id}")
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Plant API client.
        
        Args:
            base_url: Plant API base URL (defaults to PLANT_API_URL from settings)
            timeout: Request timeout in seconds (default 30)
            max_retries: Maximum retry attempts (default 3)
        """
        self.base_url = base_url or getattr(settings, "plant_base_url", None) or getattr(settings, "PLANT_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing."""
        return str(uuid.uuid4())
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True
    )
    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        correlation_id: Optional[str] = None
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic and correlation ID.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /api/v1/agents)
            json_data: Request body (for POST/PUT)
            params: Query parameters
            headers: Additional headers
            correlation_id: Correlation ID (auto-generated if not provided)
        
        Returns:
            HTTP response
        
        Raises:
            PlantAPIError: On request failure after retries
        """
        url = f"{self.base_url}{path}"
        
        # Build headers with correlation ID
        request_headers = {
            "Content-Type": "application/json",
            "X-Correlation-ID": correlation_id or self._generate_correlation_id(),
            **(headers or {})
        }
        
        response = await self.client.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            headers=request_headers
        )
        
        return response
    
    def _parse_error(self, response: httpx.Response) -> Exception:
        """
        Parse RFC 7807 error response into appropriate exception.
        
        Args:
            response: HTTP error response
        
        Returns:
            Appropriate exception type based on status code and error type
        """
        try:
            error_data = response.json()
            error = ErrorResponse(error_data)
        except Exception:
            # Fallback if response is not JSON
            return PlantAPIError(f"HTTP {response.status_code}: {response.text}")
        
        # Map to specific exception types
        if response.status_code == 404:
            return EntityNotFoundError(error.detail)
        elif response.status_code == 409:
            return DuplicateEntityError(error.detail)
        elif response.status_code == 422:
            if "constitutional" in error.type.lower():
                return ConstitutionalAlignmentError(
                    f"{error.detail}\nViolations: {', '.join(error.violations)}"
                )
            else:
                return ValidationError(
                    f"{error.detail}\nViolations: {', '.join(error.violations)}"
                )
        else:
            return PlantAPIError(f"{error.title}: {error.detail}")

    # ========== AGENT TYPE DEFINITIONS (Phase 1) ==========

    async def list_agent_type_definitions(
        self,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> list[dict]:
        response = await self._request(
            method="GET",
            path="/api/v1/agent-types",
            json_data=None,
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id,
        )

        if response.status_code == 200:
            return response.json()
        raise self._parse_error(response)

    async def get_agent_type_definition(
        self,
        agent_type_id: str,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> dict:
        response = await self._request(
            method="GET",
            path=f"/api/v1/agent-types/{agent_type_id}",
            json_data=None,
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id,
        )

        if response.status_code == 200:
            return response.json()
        raise self._parse_error(response)

    async def upsert_agent_type_definition(
        self,
        agent_type_id: str,
        payload: dict,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> dict:
        response = await self._request(
            method="PUT",
            path=f"/api/v1/agent-types/{agent_type_id}",
            json_data=payload,
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id,
        )

        if response.status_code == 200:
            return response.json()
        raise self._parse_error(response)
    
    # ========== GENESIS ENDPOINTS (Skills) ==========
    
    async def create_skill(
        self,
        skill_data: SkillCreate,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> SkillResponse:
        """
        Create new skill (pending Genesis certification).
        
        Args:
            skill_data: Skill creation data
            correlation_id: Optional correlation ID for tracing
        
        Returns:
            Created skill entity
        
        Raises:
            DuplicateEntityError: If skill already exists
            ConstitutionalAlignmentError: If L0/L1 validation fails
            ValidationError: If request validation fails
        """
        response = await self._request(
            method="POST",
            path="/api/v1/genesis/skills",
            json_data=skill_data.dict(),
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 201:
            return SkillResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def list_skills(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> List[SkillResponse]:
        """
        List all skills with optional filtering.
        
        Args:
            category: Filter by category (technical/soft_skill/domain_expertise)
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)
            correlation_id: Optional correlation ID
        
        Returns:
            List of skill entities
        """
        params = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        
        response = await self._request(
            method="GET",
            path="/api/v1/genesis/skills",
            params=params,
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return [SkillResponse(skill) for skill in response.json()]
        else:
            raise self._parse_error(response)
    
    async def get_skill(
        self,
        skill_id: str,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> SkillResponse:
        """
        Get skill by ID.
        
        Args:
            skill_id: Skill UUID
            correlation_id: Optional correlation ID
        
        Returns:
            Skill entity
        
        Raises:
            EntityNotFoundError: If skill doesn't exist
        """
        response = await self._request(
            method="GET",
            path=f"/api/v1/genesis/skills/{skill_id}",
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return SkillResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def certify_skill(
        self,
        skill_id: str,
        certification_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> SkillResponse:
        """
        Certify skill via Genesis workflow.
        
        Args:
            skill_id: Skill UUID
            certification_data: Optional certification notes/metadata
            correlation_id: Optional correlation ID
        
        Returns:
            Certified skill entity
        
        Raises:
            EntityNotFoundError: If skill doesn't exist
            ConstitutionalAlignmentError: If certification requirements not met
        """
        response = await self._request(
            method="POST",
            path=f"/api/v1/genesis/skills/{skill_id}/certify",
            json_data=certification_data or {},
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return SkillResponse(response.json())
        else:
            raise self._parse_error(response)
    
    # ========== GENESIS ENDPOINTS (Job Roles) ==========
    
    async def create_job_role(
        self,
        job_role_data: JobRoleCreate,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> JobRoleResponse:
        """
        Create new job role (pending Genesis certification).
        
        Args:
            job_role_data: Job role creation data
            correlation_id: Optional correlation ID
        
        Returns:
            Created job role entity
        
        Raises:
            DuplicateEntityError: If job role already exists
            ConstitutionalAlignmentError: If L0/L1 validation fails
            ValidationError: If request validation fails
        """
        response = await self._request(
            method="POST",
            path="/api/v1/genesis/job-roles",
            json_data=job_role_data.dict(),
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 201:
            return JobRoleResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def list_job_roles(
        self,
        limit: int = 100,
        offset: int = 0,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> List[JobRoleResponse]:
        """
        List all job roles with pagination.
        
        Args:
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)
            correlation_id: Optional correlation ID
        
        Returns:
            List of job role entities
        """
        response = await self._request(
            method="GET",
            path="/api/v1/genesis/job-roles",
            params={"limit": limit, "offset": offset},
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return [JobRoleResponse(role) for role in response.json()]
        else:
            raise self._parse_error(response)
    
    async def get_job_role(
        self,
        job_role_id: str,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> JobRoleResponse:
        """
        Get job role by ID.
        
        Args:
            job_role_id: Job role UUID
            correlation_id: Optional correlation ID
        
        Returns:
            Job role entity
        
        Raises:
            EntityNotFoundError: If job role doesn't exist
        """
        response = await self._request(
            method="GET",
            path=f"/api/v1/genesis/job-roles/{job_role_id}",
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return JobRoleResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def certify_job_role(
        self,
        job_role_id: str,
        certification_data: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> JobRoleResponse:
        """
        Certify job role via Genesis workflow.
        
        Args:
            job_role_id: Job role UUID
            certification_data: Optional certification notes/metadata
            correlation_id: Optional correlation ID
        
        Returns:
            Certified job role entity
        
        Raises:
            EntityNotFoundError: If job role doesn't exist
            ConstitutionalAlignmentError: If certification requirements not met
        """
        response = await self._request(
            method="POST",
            path=f"/api/v1/genesis/job-roles/{job_role_id}/certify",
            json_data=certification_data or {},
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return JobRoleResponse(response.json())
        else:
            raise self._parse_error(response)
    
    # ========== AGENT ENDPOINTS ==========
    
    async def create_agent(
        self,
        agent_data: AgentCreate,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> AgentResponse:
        """
        Create new agent with industry locking.
        
        Args:
            agent_data: Agent creation data
            correlation_id: Optional correlation ID
        
        Returns:
            Created agent entity
        
        Raises:
            EntityNotFoundError: If referenced skill/job_role/industry doesn't exist
            ConstitutionalAlignmentError: If L0/L1 validation fails
            ValidationError: If request validation fails
        """
        response = await self._request(
            method="POST",
            path="/api/v1/agents",
            json_data=agent_data.dict(),
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 201:
            return AgentResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def list_agents(
        self,
        industry: Optional[str] = None,
        industry_id: Optional[str] = None,
        job_role_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> List[AgentResponse]:
        """
        List all agents with optional filtering.
        
        Args:
            industry_id: Filter by industry UUID
            job_role_id: Filter by job role UUID
            limit: Maximum results (default 100)
            offset: Pagination offset (default 0)
            correlation_id: Optional correlation ID
        
        Returns:
            List of agent entities
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        # Prefer modern filter keys where available.
        if industry is not None:
            params["industry"] = industry
        elif industry_id is not None:
            params["industry_id"] = industry_id
        if job_role_id is not None:
            params["job_role_id"] = job_role_id
        if status is not None:
            params["status"] = status
        
        response = await self._request(
            method="GET",
            path="/api/v1/agents",
            params=params,
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return [AgentResponse(agent) for agent in response.json()]
        else:
            raise self._parse_error(response)
    
    async def get_agent(
        self,
        agent_id: str,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> AgentResponse:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent UUID
            correlation_id: Optional correlation ID
        
        Returns:
            Agent entity
        
        Raises:
            EntityNotFoundError: If agent doesn't exist
        """
        response = await self._request(
            method="GET",
            path=f"/api/v1/agents/{agent_id}",
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return AgentResponse(response.json())
        else:
            raise self._parse_error(response)
    
    async def assign_agent_to_team(
        self,
        agent_id: str,
        team_id: str,
        correlation_id: Optional[str] = None,
        auth_header: Optional[str] = None,
    ) -> AgentResponse:
        """
        Assign agent to team.
        
        Args:
            agent_id: Agent UUID
            team_id: Team UUID
            correlation_id: Optional correlation ID
        
        Returns:
            Updated agent entity
        
        Raises:
            EntityNotFoundError: If agent or team doesn't exist
        """
        response = await self._request(
            method="POST",
            path=f"/api/v1/agents/{agent_id}/assign-team",
            json_data={"team_id": team_id},
            headers={"Authorization": auth_header} if auth_header else None,
            correlation_id=correlation_id
        )
        
        if response.status_code == 200:
            return AgentResponse(response.json())
        else:
            raise self._parse_error(response)


# Singleton instance for dependency injection
_plant_client: Optional[PlantAPIClient] = None


def get_plant_client() -> PlantAPIClient:
    """
    Get singleton Plant API client instance.
    
    Used as FastAPI dependency:
        @router.post("/genesis/skills")
        async def create_skill(
            skill_data: SkillCreate,
            plant_client: PlantAPIClient = Depends(get_plant_client)
        ):
            skill = await plant_client.create_skill(skill_data)
            return skill
    
    Returns:
        PlantAPIClient instance
    """
    global _plant_client
    if _plant_client is None:
        _plant_client = PlantAPIClient()
    return _plant_client


async def close_plant_client():
    """Close Plant API client connection."""
    global _plant_client
    if _plant_client is not None:
        await _plant_client.close()
        _plant_client = None
