"""
Factory for creating Vector DB provider instances
"""

import logging
from typing import Optional
from .base import VectorDBProvider
from .providers.in_memory_provider import InMemoryProvider
from .providers.chromadb_provider import ChromaDBProvider
from .providers.qdrant_provider import QdrantProvider

logger = logging.getLogger(__name__)


class VectorDBFactory:
    """Factory for creating vector database providers"""
    
    @staticmethod
    def create(
        provider_type: str = "in-memory",
        **kwargs
    ) -> Optional[VectorDBProvider]:
        """
        Create a vector database provider
        
        Args:
            provider_type: Type of provider ('in-memory', 'chromadb', 'pinecone')
            **kwargs: Provider-specific configuration
            
        Returns:
            VectorDBProvider instance or None if creation failed
        """
        logger.info(f"🏭 Creating vector DB provider: {provider_type}")
        
        try:
            if provider_type == "in-memory":
                return InMemoryProvider()
            
            elif provider_type == "chromadb":
                persist_dir = kwargs.get('persist_directory', './data/chromadb')
                return ChromaDBProvider(persist_directory=persist_dir)
            
            elif provider_type == "qdrant":
                host = kwargs.get('host', 'localhost')
                port = kwargs.get('port', 6333)
                return QdrantProvider(host=host, port=port)
            
            else:
                logger.error(f"❌ Unknown provider type: {provider_type}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to create provider: {e}")
            return None
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of available providers"""
        return ['in-memory', 'chromadb', 'qdrant']
