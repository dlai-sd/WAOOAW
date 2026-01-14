"""Seed script for Plant backend sample data (~50 records).

Run after applying migrations:
    uvicorn not required; execute directly:
        python -m database.seed_data
"""
from __future__ import annotations

import asyncio
import random
from typing import List

from core.database import get_connector
from models.team import Agent, Industry, Team
from models.skill import Skill
from models.job_role import JobRole


INDUSTRIES = [
    {"name": "Marketing", "description": "Growth, content, and performance"},
    {"name": "Education", "description": "Tutoring and academic support"},
    {"name": "Sales", "description": "Revenue and pipeline acceleration"},
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

    async with connector.get_session() as session:
        # Industries
        industry_objs: List[Industry] = []
        for industry in INDUSTRIES:
            obj = Industry(
                name=industry["name"],
                description=industry["description"],
                tags=[industry["name"].lower()],
            )
            industry_objs.append(obj)
            session.add(obj)
        await session.flush()

        # Skills
        skill_objs: List[Skill] = []
        for name, category in SKILLS:
            skill = Skill(
                name=name,
                description=f"{name} capability",
                category=category,
                tags=[category],
            )
            skill_objs.append(skill)
            session.add(skill)
        await session.flush()

        # Job Roles
        job_role_objs: List[JobRole] = []
        for name, skill_names in JOB_ROLES:
            skill_ids = [s.id for s in skill_objs if s.name in skill_names]
            jr = JobRole(
                name=name,
                description=f"{name} role",
                required_skills=skill_ids,
                seniority_level=random.choice(["junior", "mid", "senior"]),
                industry_id=random.choice(industry_objs).id,
                tags=["role"],
            )
            job_role_objs.append(jr)
            session.add(jr)
        await session.flush()

        # Teams
        team_objs: List[Team] = []
        for idx, jr in enumerate(job_role_objs[:6]):
            team = Team(
                name=f"Team {idx+1}",
                description=f"Specialized team for {jr.name}",
                job_role_id=jr.id,
                industry_id=jr.industry_id,
                tags=["team"],
            )
            team_objs.append(team)
            session.add(team)
        await session.flush()

        # Agents
        agent_count = 0
        for agent_name in AGENTS:
            skill = random.choice(skill_objs)
            jr = random.choice(job_role_objs)
            industry = random.choice(industry_objs)
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
            agent_count += 1
        await session.commit()

    await connector.close()
    print("Seed data inserted:", len(INDUSTRIES), "industries,", len(SKILLS), "skills,", len(JOB_ROLES), "job roles,", len(AGENTS), "agents")


if __name__ == "__main__":
    asyncio.run(seed())
