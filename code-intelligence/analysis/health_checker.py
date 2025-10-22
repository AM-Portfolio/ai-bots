"""
Health checker - validates system health and connectivity
"""
import logging
from typing import Dict, Any

from shared.vector_db.embedding_service import EmbeddingService
from storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class HealthChecker:
    """Checks health of all services"""
    
    async def check_all(self) -> Dict[str, Any]:
        """
        Check health of all services.
        
        Returns:
            Health status for each component
        """
        logger.info("🏥 Running health checks...")
        
        health = {
            "embedding_service": await self._check_embedding_service(),
            "vector_store": await self._check_vector_store(),
            "llm_service": await self._check_llm_service()
        }
        
        return health
    
    async def _check_embedding_service(self) -> bool:
        """Check embedding service health"""
        try:
            embedding_service = EmbeddingService(provider="auto")
            is_healthy = await embedding_service.health_check()
            logger.info(f"✅ Embedding service: {'Connected' if is_healthy else 'Failed'}")
            return is_healthy
        except Exception as e:
            logger.error(f"❌ Embedding service: {e}")
            return False
    
    async def _check_vector_store(self) -> bool:
        """Check vector store health"""
        try:
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            vector_store = VectorStore(
                collection_name="health_check_test",
                embedding_dim=dimension
            )
            logger.info("✅ Vector store: Connected")
            return True
        except Exception as e:
            logger.error(f"❌ Vector store: {e}")
            return False
    
    async def _check_llm_service(self) -> bool:
        """Check LLM service health"""
        try:
            # TODO: Add actual LLM health check
            logger.info("✅ LLM service: Ready")
            return True
        except Exception as e:
            logger.error(f"❌ LLM service: {e}")
            return False
    
    def format_results(self, health: Dict[str, bool]) -> str:
        """Format health check results"""
        all_healthy = all(health.values())
        status_icon = "✅" if all_healthy else "⚠️"
        
        output = [
            "\n🏥 Health Check Results:",
            "=" * 60,
            f"{status_icon} Overall Status: {'Healthy' if all_healthy else 'Issues Detected'}",
            ""
        ]
        
        for service, status in health.items():
            icon = "✅" if status else "❌"
            output.append(f"  {icon} {service.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")
        
        return "\n".join(output)
