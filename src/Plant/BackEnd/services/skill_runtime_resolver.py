"""SkillRuntimeResolver — bridges DB entities to the typed runtime pipeline.

PLANT-RUNTIME-1 E1

Given a goal_instance_id or hired_instance_id, resolves:
1. The AgentSpec (with ConstructBindings) via AgentSpecRegistry
2. The goal_config (customer's saved configuration from AgentSkillModel.goal_config)

This is the convergence bridge between:
  - Persistence layer: HiredAgentModel, GoalInstanceModel, AgentSkillModel
  - Runtime layer: GoalSchedulerService typed pump→processor pipeline
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import PiiMaskingFilter, get_logger

logger = get_logger(__name__)


class SkillRuntimeBundle:
    """Runtime bundle resolved for a goal execution.

    Carries everything GoalSchedulerService._execute_goal needs to dispatch
    via the typed pump→processor pipeline (PLANT-MOULD-1).
    """

    __slots__ = ("agent_spec", "goal_config", "hired_instance_id", "agent_type_id")

    def __init__(
        self,
        *,
        agent_spec: Any,           # agent_mold.spec.AgentSpec
        goal_config: dict[str, Any],
        hired_instance_id: str,
        agent_type_id: str,
    ) -> None:
        self.agent_spec = agent_spec
        self.goal_config = goal_config
        self.hired_instance_id = hired_instance_id
        self.agent_type_id = agent_type_id

    def __repr__(self) -> str:
        return (
            f"<SkillRuntimeBundle agent_type_id={self.agent_type_id!r} "
            f"hired_instance_id={self.hired_instance_id!r} "
            f"has_bindings={self.agent_spec.bindings is not None}>"
        )


class SkillRuntimeResolver:
    """Resolves AgentSpec + goal_config for a given goal run.

    Resolution chain:
      goal_instance_id → GoalInstanceModel → hired_instance_id
      hired_instance_id → HiredAgentModel  → agent_type_id, agent_id
      agent_type_id     → AgentSpecRegistry → AgentSpec (with ConstructBindings)
      agent_id          → AgentSkillModel (primary=True) → goal_config JSONB

    Soft failures:
    - Returns None when any step in the chain cannot be resolved.
    - Callers must fall back to the legacy (NotImplementedError) path when None is returned.

    Usage:
        resolver = SkillRuntimeResolver(db)
        bundle = await resolver.resolve_for_goal("goal-uuid-1")
        if bundle:
            result = await scheduler._execute_goal(
                goal_instance_id="goal-uuid-1",
                agent_spec=bundle.agent_spec,
                goal_config=bundle.goal_config,
                hired_agent_id=bundle.hired_instance_id,
            )
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _spec_registry(self):
        from agent_mold.registry import AgentSpecRegistry
        return AgentSpecRegistry.instance()

    async def resolve_for_goal(
        self, goal_instance_id: str
    ) -> Optional[SkillRuntimeBundle]:
        """Resolve AgentSpec + goal_config from a goal_instance_id.

        Returns None when the goal instance, hired agent, or agent spec cannot
        be resolved.  Callers should treat None as "fall back to legacy path".
        """
        from models.hired_agent import GoalInstanceModel, HiredAgentModel
        from models.agent_skill import AgentSkillModel

        # 1. GoalInstanceModel → hired_instance_id
        goal_row = (
            await self._db.execute(
                select(GoalInstanceModel).where(
                    GoalInstanceModel.goal_instance_id == goal_instance_id
                )
            )
        ).scalar_one_or_none()

        if goal_row is None:
            logger.debug(
                "skill_runtime_resolve_miss reason=goal_not_found "
                "goal_instance_id=%s",
                goal_instance_id,
            )
            return None

        return await self._resolve_from_hired_instance(
            goal_row.hired_instance_id,
            HiredAgentModel=HiredAgentModel,
            AgentSkillModel=AgentSkillModel,
        )

    async def resolve_for_hired_agent(
        self, hired_instance_id: str
    ) -> Optional[SkillRuntimeBundle]:
        """Resolve AgentSpec + goal_config directly from a hired_instance_id.

        Used when goal_instance_id is unavailable (e.g. direct scheduler triggers).
        Returns None on any resolution failure.
        """
        from models.hired_agent import HiredAgentModel
        from models.agent_skill import AgentSkillModel

        return await self._resolve_from_hired_instance(
            hired_instance_id,
            HiredAgentModel=HiredAgentModel,
            AgentSkillModel=AgentSkillModel,
        )

    async def _resolve_from_hired_instance(
        self,
        hired_instance_id: str,
        *,
        HiredAgentModel: Any,
        AgentSkillModel: Any,
    ) -> Optional[SkillRuntimeBundle]:
        """Internal: resolve bundle from a hired_instance_id."""
        # 2. HiredAgentModel → agent_type_id + agent_id
        hired_row = (
            await self._db.execute(
                select(HiredAgentModel).where(
                    HiredAgentModel.hired_instance_id == hired_instance_id
                )
            )
        ).scalar_one_or_none()

        if hired_row is None:
            logger.debug(
                "skill_runtime_resolve_miss reason=hired_agent_not_found "
                "hired_instance_id=%s",
                hired_instance_id,
            )
            return None

        agent_type_id = hired_row.agent_type_id
        if not agent_type_id:
            logger.debug(
                "skill_runtime_resolve_miss reason=no_agent_type_id "
                "hired_instance_id=%s",
                hired_instance_id,
            )
            return None

        # 3. AgentSpecRegistry → AgentSpec
        spec = self._spec_registry().get_spec(agent_type_id)
        if spec is None:
            logger.debug(
                "skill_runtime_resolve_miss reason=spec_not_in_registry "
                "agent_type_id=%s",
                agent_type_id,
            )
            return None

        # 4. AgentSkillModel (primary=True) → goal_config
        goal_config: dict[str, Any] = {}
        agent_id = getattr(hired_row, "agent_id", None)
        if agent_id:
            try:
                import uuid as _uuid
                agent_uuid = _uuid.UUID(str(agent_id))
                skill_row = (
                    await self._db.execute(
                        select(AgentSkillModel)
                        .where(AgentSkillModel.agent_id == agent_uuid)
                        .where(AgentSkillModel.is_primary.is_(True))
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if skill_row is not None and skill_row.goal_config:
                    goal_config = dict(skill_row.goal_config)
            except (ValueError, TypeError):
                # agent_id is not a valid UUID — skip goal_config resolution
                pass

        logger.debug(
            "skill_runtime_resolve_ok agent_type_id=%s hired_instance_id=%s "
            "has_bindings=%s goal_config_keys=%s",
            agent_type_id,
            hired_instance_id,
            spec.bindings is not None,
            sorted(goal_config.keys()),
        )

        return SkillRuntimeBundle(
            agent_spec=spec,
            goal_config=goal_config,
            hired_instance_id=hired_instance_id,
            agent_type_id=agent_type_id,
        )
