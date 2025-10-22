"""
Embedding Service for generating vector embeddings
Uses Together AI embeddings with fallback to hash-based approach
"""

import logging
import os
import hashlib
import struct
from typing import List, Optional
from together import Together

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings with Together AI and hash fallback"""
    
    def __init__(self, provider: str = "auto"):
        """
        Initialize embedding service with role-based provider selection
        
        Args:
            provider: LLM provider to use ('auto', 'azure', 'together')
        """
        from shared.config import settings
        from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator
        
        # Get provider based on role
        if provider == "auto":
            orchestrator = get_resilient_orchestrator()
            provider = orchestrator.get_provider_for_role("embedding")
        
        self.provider_name = provider
        self.dimension = 768
        self.fallback_dimension = 768
        self.client = None
        self.api_available = False
        
        # Set model based on provider
        if provider == "azure":
            self.embedding_model = settings.azure_openai_embedding_deployment
            self._initialize_azure_client()
        else:
            self.embedding_model = "togethercomputer/m2-bert-80M-32k-retrieval"
            self._initialize_together_client()
        
        logger.info(f"🎯 Initializing embedding service with provider: {provider}")
        logger.info(f"   • Model: {self.embedding_model}")
        logger.info(f"   • API Available: {self.api_available}")
        logger.info(f"   • Fallback: Hash-based embeddings")
    
    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client for embeddings"""
        try:
            from shared.config import settings
            from openai import AzureOpenAI
            
            if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
                logger.warning("⚠️  Azure OpenAI credentials not configured, using fallback embeddings")
                return
            
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.api_available = True
            logger.info("✅ Azure OpenAI embedding client initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Azure OpenAI client: {e}")
            logger.info("🔄 Will use hash-based fallback embeddings")
            self.client = None
            self.api_available = False
    
    def _initialize_together_client(self):
        """Initialize Together AI client for embeddings"""
        try:
            api_key = os.environ.get("TOGETHER_API_KEY")
            if not api_key:
                logger.warning("⚠️  TOGETHER_API_KEY not found, using fallback embeddings only")
                return
            
            # Set environment variable for Together client (it reads from env)
            if api_key and not os.environ.get("TOGETHER_API_KEY"):
                os.environ["TOGETHER_API_KEY"] = api_key
            
            self.client = Together()
            self.api_available = True
            logger.info("✅ Together AI embedding client initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Together AI client: {e}")
            logger.info("🔄 Will use hash-based fallback embeddings")
            self.client = None
            self.api_available = False
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using configured provider with fallback to hash-based approach
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (768 dimensions)
        """
        # Try configured provider (Azure or Together)
        if self.api_available and self.client:
            try:
                if self.provider_name == "azure":
                    # Azure OpenAI embeddings
                    response = self.client.embeddings.create(
                        model=self.embedding_model,
                        input=text
                    )
                    embedding = response.data[0].embedding
                else:
                    # Together AI embeddings - use direct REST API as SDK has issues
                    import requests
                    api_key = os.environ.get("TOGETHER_API_KEY")
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": self.embedding_model,
                        "input": text
                    }
                    response = requests.post(
                        "https://api.together.xyz/v1/embeddings",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                    response.raise_for_status()
                    embedding = response.json()["data"][0]["embedding"]
                
                logger.debug(f"✅ Generated {self.provider_name} embedding (dim: {len(embedding)})")
                
                # Ensure consistent dimensions
                if len(embedding) > self.dimension:
                    embedding = embedding[:self.dimension]
                elif len(embedding) < self.dimension:
                    embedding.extend([0.0] * (self.dimension - len(embedding)))
                
                return embedding
                
            except Exception as e:
                logger.warning(f"⚠️  {self.provider_name} embedding failed: {e}")
                logger.info("🔄 Falling back to hash-based embeddings")
                # Continue to fallback method
        
        # Fallback to hash-based embeddings
        return self._generate_hash_embedding(text)
    
    def _generate_hash_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic hash-based embedding as fallback
        
        Args:
            text: Text to embed
            
        Returns:
            Hash-based embedding vector
        """
        try:
            # Create deterministic embedding from text hash
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert hash bytes to float vector
            embedding = []
            for i in range(0, len(hash_bytes), 4):
                chunk = hash_bytes[i:i+4]
                if len(chunk) == 4:
                    val = struct.unpack('f', chunk)[0]
                    embedding.append(val)
            
            # Pad to required dimensions
            while len(embedding) < self.fallback_dimension:
                embedding.append(0.0)
            
            logger.debug(f"🔄 Generated fallback hash embedding (dim: {len(embedding[:self.fallback_dimension])})")
            return embedding[:self.fallback_dimension]
            
        except Exception as e:
            logger.error(f"❌ Failed to generate fallback embedding: {e}")
            # Return zero vector on complete failure
            return [0.0] * self.fallback_dimension
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with intelligent batching
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        together_success = 0
        fallback_used = 0
        
        # Try batch processing with Together AI first
        if self.api_available and self.client and len(texts) > 1:
            try:
                # Together AI supports batch processing
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                
                for data_point in response.data:
                    embedding = data_point.embedding
                    # Ensure consistent dimensions
                    if len(embedding) > self.dimension:
                        embedding = embedding[:self.dimension]
                    elif len(embedding) < self.dimension:
                        embedding.extend([0.0] * (self.dimension - len(embedding)))
                    embeddings.append(embedding)
                
                together_success = len(embeddings)
                logger.info(f"✅ Generated {together_success} Together AI embeddings in batch")
                return embeddings
                
            except Exception as e:
                logger.warning(f"⚠️  Together AI batch embedding failed: {e}")
                logger.info("🔄 Falling back to individual processing")
        
        # Fallback: Process individually
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
            
            # Track method used (check if it's likely a hash-based embedding)
            if embedding and len(set(embedding[-10:])) <= 2:  # Hash embeddings often have repeated values
                fallback_used += 1
            else:
                together_success += 1
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        if together_success > 0:
            logger.info(f"   • Together AI: {together_success}")
        if fallback_used > 0:
            logger.info(f"   • Hash fallback: {fallback_used}")
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model and status"""
        return {
            "provider": self.provider_name,
            "model": self.embedding_model,
            "dimension": self.dimension,
            "api_available": self.api_available,
            "fallback_enabled": True,
            "fallback_method": "hash-based"
        }
    
    async def health_check(self) -> dict:
        """Check the health of the embedding service"""
        status = {
            "service": "embedding",
            "provider": self.provider_name,
            "model": self.embedding_model,
            "api_available": self.api_available,
            "fallback_available": True
        }
        
        # Test Together AI if available
        if self.api_available and self.client:
            try:
                test_response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input="health check"
                )
                status["together_ai_status"] = "healthy"
                status["together_ai_dimension"] = len(test_response.data[0].embedding)
            except Exception as e:
                status["together_ai_status"] = f"error: {str(e)}"
                status["api_available"] = False
                self.api_available = False
        else:
            status["together_ai_status"] = "not_configured"
        
        # Test fallback
        try:
            fallback_embedding = self._generate_hash_embedding("health check")
            status["fallback_status"] = "healthy"
            status["fallback_dimension"] = len(fallback_embedding)
        except Exception as e:
            status["fallback_status"] = f"error: {str(e)}"
        
        return status
