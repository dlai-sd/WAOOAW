"""Seed script for Plant backend sample data (~50 records).

Run after applying migrations:
    uvicorn not required; execute directly:
        python -m database.seed_data
"""
from __future__ import annotations

import asyncio
import random
from typing import Dict, List

from sqlalchemy import select

from core.database import get_connector
from models.team import Agent, Industry, Team
from models.skill import Skill
from models.job_role import JobRole


INDUSTRIES = [
    {"name": "Marketing", "description": "Growth, content, and performance"},
    {"name": "Education", "description": "Tutoring and academic support"},
    {"name": "Sales", "description": "Revenue and pipeline acceleration"},
    {"name": "Platform", "description": "Internal platform governance and enablement"},
]

SKILLS = [
    ("Content Marketing", "technical"),
    ("Social Media", "technical"),
    ("SEO", "technical"),
    ("Email Marketing", "technical"),
    ("PPC Advertising", "technical"),
    ("Brand Strategy", "domain_expertise"),
    ("Influencer Marketing", "technical"),
    ("Math Tutoring", "domain_expertise"),
    ("Science Tutoring", "domain_expertise"),
    ("English Coaching", "domain_expertise"),
    ("Test Prep", "domain_expertise"),
    ("Career Counseling", "soft_skill"),
    ("Study Planning", "soft_skill"),
    ("Homework Help", "soft_skill"),
    ("SDR Prospecting", "technical"),
    ("Account Executive", "technical"),
    ("CRM Management", "technical"),
    ("Sales Enablement", "technical"),
    ("Lead Generation", "technical"),

    # Internal platform skills (seeded so Plant can host internal blueprint agents)
    ("Governance Gatekeeping", "domain_expertise"),
    ("Skill Certification", "domain_expertise"),
    ("Job Role Certification", "domain_expertise"),
    ("Policy Enforcement", "domain_expertise"),
    ("Precedent Seed Review", "domain_expertise"),

    ("Architecture Review", "domain_expertise"),
    ("API Contract Design", "technical"),
    ("Threat Modeling (STRIDE)", "domain_expertise"),
    ("Performance Budgeting", "domain_expertise"),
    ("ADR Authoring", "domain_expertise"),

    ("User Story Writing", "domain_expertise"),
    ("User Journey Mapping", "domain_expertise"),
    ("Acceptance Criteria", "domain_expertise"),
    ("Requirements Traceability", "domain_expertise"),
    ("Prioritization", "soft_skill"),
]

JOB_ROLES = [
    ("Content Strategist", ["Content Marketing", "Brand Strategy"]),
    ("SEO Specialist", ["SEO", "PPC Advertising"]),
    ("Social Media Manager", ["Social Media", "Influencer Marketing"]),
    ("Email Marketer", ["Email Marketing", "Content Marketing"]),
    ("Math Tutor", ["Math Tutoring", "Homework Help"]),
    ("Science Tutor", ["Science Tutoring", "Study Planning"]),
    ("English Tutor", ["English Coaching", "Homework Help"]),
    ("Test Prep Coach", ["Test Prep", "Study Planning"]),
    ("SDR", ["SDR Prospecting", "Lead Generation", "CRM Management"]),
    ("Account Executive", ["Account Executive", "Sales Enablement"]),

    # Internal platform job roles (Platform industry)
    (
        "Platform Governance Certifier",
        [
            "Governance Gatekeeping",
            "Skill Certification",
            "Job Role Certification",
            "Policy Enforcement",
            "Precedent Seed Review",
        ],
    ),
    (
        "Platform Systems Architect",
        [
            "Architecture Review",
            "API Contract Design",
            "Threat Modeling (STRIDE)",
            "Performance Budgeting",
            "ADR Authoring",
        ],
    ),
    (
        "Platform Business Analyst",
        [
            "User Story Writing",
            "User Journey Mapping",
            "Acceptance Criteria",
            "Requirements Traceability",
            "Prioritization",
        ],
    ),
]


INTERNAL_PLATFORM_AGENTS = [
    {
        "name": "Genesis",
        "job_role": "Platform Governance Certifier",
        "primary_skill": "Governance Gatekeeping",
        "industry": "Platform",
        "tags": ["internal", "governance", "foundational"],
    },
    {
        "name": "Systems Architect",
        "job_role": "Platform Systems Architect",
        "primary_skill": "Architecture Review",
        "industry": "Platform",
        "tags": ["internal", "architecture", "foundational"],
    },
    {
        "name": "Business Analyst",
        "job_role": "Platform Business Analyst",
        "primary_skill": "User Story Writing",
        "industry": "Platform",
        "tags": ["internal", "product", "platform"],
    },
]

AGENTS = [
    "Ava Flux", "Nova Quill", "Orion Sage", "Lumen Drift", "Echo Vale",
    "Mira Pulse", "Coda Trace", "Ivy Loom", "Vega March", "Rune Shift",
    "Aria North", "Sage Wren", "Kai Ember", "Lux Harbor", "Zane Frost",
    "Faye Lark", "Nia Cove", "Juno Kade", "Ezra Bloom", "Rhea Sparks",
    "Pax Arden", "Lyra Crest", "Theo March", "Indi Ray", "Vale Knox",
    "Remy Slate", "Bria Vaughn", "Zuri Lane", "Odin Crest", "Marlowe Finch",
    "Cleo Pierce", "Rowan Gale", "Tess Hart", "Ash Calder", "Siena Rush",
    "Neo Plume", "Arden Vale", "Iris Calder", "Keir Moss", "Sloane Pike",
    "Ember Knox", "Talon Rhys", "Lara Voss", "Quinn Vale", "Riven Storm",
    "Solene Ash", "Tara Wisp", "Jade Arden", "Noor Pryce", "Opal Winn",
]


async def seed() -> None:
    connector = get_connector()
    await connector.initialize()

    session = await connector.get_session()
    try:
        # Industries (idempotent by name)
        industry_by_name: Dict[str, Industry] = {}
        for industry in INDUSTRIES:
            name = industry["name"]
            existing = (
                await session.execute(select(Industry).where(Industry.name == name))
            ).scalar_one_or_none()
            if existing:
                industry_by_name[name] = existing
                continue

            obj = Industry(
                name=name,
                description=industry["description"],
                tags=[name.lower()],
            )
            session.add(obj)
            industry_by_name[name] = obj
        await session.flush()

        # Skills (idempotent by name)
        skill_by_name: Dict[str, Skill] = {}
        for name, category in SKILLS:
            existing = (
                await session.execute(select(Skill).where(Skill.name == name))
            ).scalar_one_or_none()
            if existing:
                skill_by_name[name] = existing
                continue

            skill = Skill(
                name=name,
                description=f"{name} capability",
                category=category,
                tags=[category],
            )
            session.add(skill)
            skill_by_name[name] = skill
        await session.flush()

        # Job Roles (idempotent by name)
        job_role_by_name: Dict[str, JobRole] = {}
        platform_industry_id = industry_by_name["Platform"].id

        for name, skill_names in JOB_ROLES:
            existing = (
                await session.execute(select(JobRole).where(JobRole.name == name))
            ).scalar_one_or_none()
            if existing:
                job_role_by_name[name] = existing
                continue

            skill_ids = [skill_by_name[s].id for s in skill_names if s in skill_by_name]
            if not skill_ids:
                raise ValueError(f"JobRole '{name}' has no resolvable required_skills")

            is_platform_role = name.startswith("Platform ")
            jr = JobRole(
                name=name,
                description=f"{name} role",
                required_skills=skill_ids,
                seniority_level=random.choice(["junior", "mid", "senior"]),
                industry_id=platform_industry_id if is_platform_role else random.choice(list(industry_by_name.values())).id,
                tags=["role"],
            )
            session.add(jr)
            job_role_by_name[name] = jr
        await session.flush()

        # Teams (best-effort idempotent by name)
        team_objs: List[Team] = []
        seed_team_roles = [r for r in job_role_by_name.values()][:6]
        for idx, jr in enumerate(seed_team_roles):
            team_name = f"Team {idx+1}"
            existing = (
                await session.execute(select(Team).where(Team.name == team_name))
            ).scalar_one_or_none()
            if existing:
                team_objs.append(existing)
                continue

            team = Team(
                name=team_name,
                description=f"Specialized team for {jr.name}",
                job_role_id=jr.id,
                industry_id=jr.industry_id,
                tags=["team"],
            )
            session.add(team)
            team_objs.append(team)
        await session.flush()

        # Agents (best-effort idempotent by name)
        agent_count_created = 0
        for agent_name in AGENTS:
            existing = (
                await session.execute(select(Agent).where(Agent.name == agent_name))
            ).scalar_one_or_none()
            if existing:
                continue

            skill = random.choice(list(skill_by_name.values()))
            jr = random.choice(list(job_role_by_name.values()))
            industry = random.choice(list(industry_by_name.values()))
            team = random.choice(team_objs) if team_objs else None
            agent = Agent(
                name=agent_name,
                skill_id=skill.id,
                job_role_id=jr.id,
                team_id=team.id if team else None,
                industry_id=industry.id,
                tags=["agent"],
            )
            session.add(agent)
            agent_count_created += 1

        # Internal platform agents (explicit, deterministic)
        for spec in INTERNAL_PLATFORM_AGENTS:
            name = spec["name"]
            existing = (
                await session.execute(select(Agent).where(Agent.name == name))
            ).scalar_one_or_none()
            if existing:
                continue

            job_role = job_role_by_name[spec["job_role"]]
            agent = Agent(
                name=name,
                skill_id=skill_by_name[spec["primary_skill"]].id,
                job_role_id=job_role.id,
                team_id=None,
                industry_id=industry_by_name[spec["industry"]].id,
                tags=["agent", *spec["tags"]],
            )
            session.add(agent)
            agent_count_created += 1

        await session.commit()
        print(
            "Seed data ensured:",
            len(INDUSTRIES),
            "industries,",
            len(SKILLS),
            "skills,",
            len(JOB_ROLES),
            "job roles,",
            "agents_created_this_run=",
            agent_count_created,
        )
    finally:
        await session.close()
        await connector.close()


if __name__ == "__main__":
    asyncio.run(seed())
