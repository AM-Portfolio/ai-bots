"""
Batch embedding generator - handles embedding generation in batches
"""
import logging
from typing import List, Dict

from utils.rate_limiter import RateLimitController, QuotaType
from shared.vector_db.embedding_service import EmbeddingService
from pipeline.code_parser import CodeChunk

logger = logging.getLogger(__name__)


class BatchEmbeddingGenerator:
    """Generates embeddings in batches with rate limiting"""
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        rate_limiter: RateLimitController
    ):
        self.embedding_service = embedding_service
        self.rate_limiter = rate_limiter
    
    async def generate_batch(
        self,
        chunks: List[CodeChunk],
        summaries: Dict[str, str]
    ) -> List[Dict]:
        """
        Generate embeddings for chunks in batches.
        
        Args:
            chunks: List of code chunks
            summaries: Dict of chunk_id -> summary text
            
        Returns:
            List of dicts with embedding data:
            {
                "chunk_id": str,
                "embedding": List[float],
                "content": str,
                "summary": str,
                "metadata": dict
            }
        """
        batch_size = self.rate_limiter.get_adaptive_batch_size(QuotaType.EMBEDDING)
        batch_size = min(batch_size, 50)  # Max 50 at a time
        
        total_chunks = len(chunks)
        embedding_data = []
        num_batches = (total_chunks + batch_size - 1) // batch_size
        
        logger.info(f"\n🔢 Generating embeddings in batches")
        logger.info(f"   Batch size: {batch_size} chunks")
        logger.info(f"   Total batches: {num_batches}")
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_chunks)
            batch = chunks[start_idx:end_idx]
            
            progress = ((batch_num + 1) / num_batches) * 100
            
            logger.info(f"\n📦 Batch {batch_num + 1}/{num_batches} ({progress:.1f}% complete)")
            logger.info(f"   Processing chunks {start_idx + 1}-{end_idx} of {total_chunks}")
            
            try:
                batch_data = await self._process_batch(batch, summaries)
                embedding_data.extend(batch_data)
                
                logger.info(f"   ✅ Batch complete: {len(batch_data)} embeddings generated")
                logger.info(f"   📊 Total progress: {len(embedding_data)}/{total_chunks} chunks")
                
            except Exception as e:
                logger.error(f"   ❌ Batch {batch_num + 1} failed: {e}")
                # Continue with next batch
        
        logger.info(f"\n✅ Embedding generation complete: {len(embedding_data)} embeddings")
        return embedding_data
    
    async def _process_batch(
        self,
        batch: List[CodeChunk],
        summaries: Dict[str, str]
    ) -> List[Dict]:
        """Process a single batch of chunks"""
        # Prepare texts (summary + code snippet)
        texts = [
            f"{summaries.get(chunk.chunk_id, '')}\n\n{chunk.content[:2000]}"
            for chunk in batch
        ]
        
        # Generate embeddings with rate limiting
        async def embed_batch():
            return await self.embedding_service.generate_embeddings_batch(texts)
        
        batch_embeddings = await self.rate_limiter.submit(
            QuotaType.EMBEDDING,
            embed_batch,
            priority=2
        )
        
        # Create embedding data structures
        embedding_data = []
        for i, chunk in enumerate(batch):
            if i < len(batch_embeddings):
                embedding_data.append({
                    "chunk_id": chunk.chunk_id,
                    "embedding": batch_embeddings[i],
                    "content": chunk.content,
                    "summary": summaries.get(chunk.chunk_id, ""),
                    "metadata": {
                        "file_path": chunk.metadata.file_path,
                        "language": chunk.metadata.language,
                        "chunk_type": chunk.metadata.chunk_type,
                        "symbol_name": chunk.metadata.symbol_name,
                        "start_line": chunk.metadata.start_line,
                        "end_line": chunk.metadata.end_line,
                        "token_count": chunk.metadata.token_count
                    }
                })
        
        return embedding_data
