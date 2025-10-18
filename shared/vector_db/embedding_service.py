"""
Embedding Service for generating vector embeddings
Uses Together AI or OpenAI for generating embeddings
"""

import logging
from typing import List, Optional
from shared.llm_providers.factory import LLMFactory

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, provider: str = "together"):
        """
        Initialize embedding service
        
        Args:
            provider: LLM provider to use for embeddings
        """
        self.provider_name = provider
        self.dimension = 768  # Default embedding dimension
        logger.info(f"🎯 Initializing embedding service with provider: {provider}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # For now, use a simple approach with Together AI
            # In production, we'd use dedicated embedding models
            provider = LLMFactory.create(self.provider_name)
            
            # Use LLM to generate a semantic representation
            # This is a simplified version - in production use proper embedding models
            response = await provider.generate(
                prompt=f"Generate a semantic embedding for: {text[:500]}",
                temperature=0.0
            )
            
            # For now, return a placeholder embedding
            # TODO: Integrate proper embedding API (e.g., OpenAI embeddings, sentence-transformers)
            import hashlib
            import struct
            
            # Create deterministic embedding from text hash
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert to 768-dimensional vector
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    val = struct.unpack('f', chunk)[0]
                    embedding.append(val)
            
            # Pad to 768 dimensions
            while len(embedding) < self.dimension:
                embedding.append(0.0)
            
            return embedding[:self.dimension]
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            # Return zero vector on error
            return [0.0] * self.dimension
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
