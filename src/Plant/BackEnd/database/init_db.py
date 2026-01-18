"""
Database initialization utilities
"""

from sqlalchemy.orm import Session
from core.database import engine, Base, SessionLocal
from core.logging import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """
    Initialize database - create all tables (development only).
    
    For production, use Alembic migrations:
        alembic upgrade head
    """
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_all_tables() -> None:
    """
    Drop all tables (DANGEROUS - development only).
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped")


def seed_genesis_data(db: Session) -> None:
    """
    Seed database with Genesis-certified baseline data.
    
    Args:
        db: Database session
    """
    from models.skill import Skill
    from models.job_role import JobRole
    import hashlib
    import json
    
    logger.info("Seeding Genesis-certified baseline data...")
    
    # Create baseline skills
    baseline_skills = [
        {
            "name": "Python 3.11",
            "description": "Backend development with Python 3.11",
            "category": "technical",
        },
        {
            "name": "FastAPI",
            "description": "Modern async web framework for APIs",
            "category": "technical",
        },
        {
            "name": "PostgreSQL",
            "description": "Relational database management",
            "category": "technical",
        },
        {
            "name": "Constitutional Alignment",
            "description": "L0/L1 principle enforcement",
            "category": "domain_expertise",
        },
    ]
    
    for skill_data in baseline_skills:
        # Check if skill already exists
        existing = db.query(Skill).filter(Skill.name == skill_data["name"]).first()
        if existing:
            logger.info(f"Skill '{skill_data['name']}' already exists, skipping")
            continue
        
        # Create version hash
        version_hash = hashlib.sha256(json.dumps(skill_data, sort_keys=True).encode()).hexdigest()
        
        skill = Skill(
            name=skill_data["name"],
            description=skill_data["description"],
            category=skill_data["category"],
            entity_type="Skill",
            governance_agent_id="genesis",
            version_hash=version_hash,
            hash_chain_sha256=[version_hash],
        )
        
        db.add(skill)
        logger.info(f"Created skill: {skill_data['name']}")
    
    db.commit()
    logger.info("Genesis baseline data seeded successfully")
