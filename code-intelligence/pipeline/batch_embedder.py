"""
Batch embedding generator - handles embedding generation in batches
"""
import logging
import sys
from typing import List, Dict

from utils.rate_limiter import RateLimitController, QuotaType
from shared.vector_db.embedding_service import EmbeddingService
from pipeline.code_parser import CodeChunk

logger = logging.getLogger(__name__)


def _print_progress_bar(current: int, total: int, prefix: str = '', bar_length: int = 50):
    """Print a progress bar to stdout (overwrites previous line)"""
    if total == 0:
        return
    
    progress = current / total
    filled = int(bar_length * progress)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    # Print with carriage return to overwrite
    sys.stdout.write(f'\r{prefix} [{bar}] {current}/{total} ({progress*100:.1f}%)')
    sys.stdout.flush()
    
    # New line when complete
    if current == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


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
        
        print(f"\n🔢 Generating embeddings for {total_chunks} chunks (batch size: {batch_size})")
        _print_progress_bar(0, total_chunks, prefix='   Progress')
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_chunks)
            batch = chunks[start_idx:end_idx]
            
            try:
                batch_data = await self._process_batch(batch, summaries)
                embedding_data.extend(batch_data)
                
                # Update progress bar
                _print_progress_bar(len(embedding_data), total_chunks, prefix='   Progress')
                
            except Exception as e:
                logger.error(f"\n   ❌ Batch {batch_num + 1} failed: {e}")
                # Continue with next batch
        
        print(f"✅ Complete: {len(embedding_data)} embeddings generated")
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
