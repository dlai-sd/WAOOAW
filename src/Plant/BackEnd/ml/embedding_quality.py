"""
Embedding Quality Monitor - drift detection + stability scoring

Architecture: Daily job via APScheduler, checks embedding stability >0.85
Reference: PLANT_BLUEPRINT Section 4.3 (Constitutional Drift Detector)
"""

from typing import List, Dict, Any
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from core.config import settings
from models.skill import Skill
from models.industry import Industry
from ml.inference_client import MLInferenceClient
from ml.embedding_cache import EmbeddingCache


logger = logging.getLogger(__name__)


class EmbeddingQualityMonitor:
    """
    Monitor embedding quality and detect drift.
    
    Responsibilities:
    - Calculate stability score (cosine similarity between old/new embeddings)
    - Detect drift (<0.85 threshold)
    - Trigger auto-regeneration
    - Alert Governor via Pub/Sub
    """
    
    def __init__(
        self,
        db: Session,
        ml_client: MLInferenceClient = None,
        cache: EmbeddingCache = None,
    ):
        self.db = db
        self.ml_client = ml_client or MLInferenceClient()
        self.cache = cache or EmbeddingCache()
        self.stability_threshold = settings.embedding_quality_stability_threshold
    
    async def check_embedding_quality(
        self,
        entity_type: str = "Skill",
    ) -> Dict[str, Any]:
        """
        Check embedding quality for all entities of type.
        
        Args:
            entity_type: Type to check (Skill or Industry)
        
        Returns:
            Quality report with drift detections
        """
        if entity_type == "Skill":
            entities = self.db.query(Skill).filter(Skill.status == "active").all()
        elif entity_type == "Industry":
            entities = self.db.query(Industry).filter(Industry.status == "active").all()
        else:
            return {"error": f"Unknown entity type: {entity_type}"}
        
        logger.info(f"Checking embedding quality for {len(entities)} {entity_type} entities")
        
        results = {
            "entity_type": entity_type,
            "total_entities": len(entities),
            "stable_count": 0,
            "drift_detected": [],
            "regenerated": [],
            "errors": [],
        }
        
        for entity in entities:
            try:
                # Get current embedding
                old_embedding = entity.embedding_384
                
                if not old_embedding:
                    logger.warning(f"Entity {entity.id} has no embedding, skipping")
                    continue
                
                # Generate fresh embedding
                text = f"{entity.name} {entity.description}" if hasattr(entity, 'description') else entity.name
                new_embedding = await self.ml_client.generate_embedding(text)
                
                # Calculate stability score (cosine similarity)
                stability = self._calculate_cosine_similarity(old_embedding, new_embedding)
                
                if stability >= self.stability_threshold:
                    results["stable_count"] += 1
                    logger.info(f"Entity {entity.id} stable: {stability:.3f}")
                else:
                    # Drift detected
                    results["drift_detected"].append({
                        "entity_id": str(entity.id),
                        "name": entity.name,
                        "stability_score": stability,
                        "threshold": self.stability_threshold,
                    })
                    
                    logger.warning(
                        f"Drift detected for {entity.name}: "
                        f"stability {stability:.3f} < {self.stability_threshold}"
                    )
                    
                    # Auto-regenerate if drift detected
                    entity.embedding_384 = new_embedding
                    entity.custom_attributes["drift_detector"] = {
                        "last_regenerated": datetime.utcnow().isoformat(),
                        "stability_score": stability,
                        "auto_regenerated": True,
                    }
                    
                    # Invalidate cache
                    self.cache.delete(text)
                    
                    results["regenerated"].append(str(entity.id))
                    
            except Exception as e:
                logger.error(f"Error checking entity {entity.id}: {str(e)}")
                results["errors"].append({
                    "entity_id": str(entity.id),
                    "error": str(e),
                })
        
        # Commit all regenerations
        self.db.commit()
        
        return results
    
    def _calculate_cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float],
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
        
        Returns:
            Similarity score (0.0 to 1.0)
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        # Cosine similarity: dot(A,B) / (norm(A) * norm(B))
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def schedule_daily_check(self):
        """
        Schedule daily embedding quality check (02:00 UTC).
        
        Uses APScheduler for background job.
        """
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        
        scheduler.add_job(
            self.check_embedding_quality,
            trigger="cron",
            hour=2,  # 02:00 UTC
            minute=0,
            args=["Skill"],
            id="skill_embedding_quality_check",
        )
        
        scheduler.add_job(
            self.check_embedding_quality,
            trigger="cron",
            hour=2,
            minute=30,
            args=["Industry"],
            id="industry_embedding_quality_check",
        )
        
        scheduler.start()
        logger.info("Scheduled daily embedding quality checks at 02:00 UTC")
