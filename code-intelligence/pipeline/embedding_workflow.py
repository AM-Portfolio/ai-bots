"""
Embedding workflow - handles the embedding generation workflow
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set

from storage.vector_store import VectorStore, EmbeddingPoint
from storage.repo_state import RepoState

logger = logging.getLogger(__name__)


class EmbeddingWorkflow:
    """Handles the complete embedding workflow: generate -> store -> update state"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    async def execute(
        self,
        embedding_data: list,
        chunks: list,
        collection_name: str,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Execute the embedding storage workflow.
        
        Args:
            embedding_data: List of embedding dictionaries
            chunks: List of chunk objects
            collection_name: Vector DB collection name
            batch_size: Batch size for storage
            
        Returns:
            Statistics about storage operation
        """
        logger.info(f"\n💾 Storing {len(embedding_data)} embeddings in vector database...")
        
        # STEP 1: Store embeddings in vector DB
        total_stored, total_failed = await self._store_embeddings(
            embedding_data=embedding_data,
            collection_name=collection_name,
            batch_size=batch_size
        )
        
        # STEP 2: Update repository state
        await self._update_repo_state(chunks)
        
        logger.info(f"✅ Stored: {total_stored}/{len(embedding_data)} embeddings")
        
        return {
            "total_stored": total_stored,
            "total_failed": total_failed,
            "success_rate": (total_stored / len(embedding_data) * 100) if embedding_data else 0
        }
    
    async def _store_embeddings(
        self,
        embedding_data: list,
        collection_name: str,
        batch_size: int
    ) -> tuple:
        """Store embeddings in vector database in batches"""
        vector_store = await VectorStore.create(
            collection_name=collection_name,
            qdrant_path=str(self.repo_path / ".qdrant")
        )
        
        # Convert to EmbeddingPoint objects
        embedding_points = [
            EmbeddingPoint(
                chunk_id=data["chunk_id"],
                embedding=data["embedding"],
                content=data["content"],
                summary=data["summary"],
                metadata=data["metadata"]
            )
            for data in embedding_data
        ]
        
        # Store in batches
        total_stored = 0
        total_failed = 0
        
        for i in range(0, len(embedding_points), batch_size):
            batch = embedding_points[i:i + batch_size]
            try:
                upsert_result = await vector_store.upsert_batch(batch)
                total_stored += upsert_result["successful"]
                total_failed += upsert_result["failed"]
            except Exception as e:
                logger.error(f"❌ Failed to store batch {i//batch_size + 1}: {e}")
                total_failed += len(batch)
        
        return total_stored, total_failed
    
    async def _update_repo_state(self, chunks: list):
        """Update repository state with processed files"""
        try:
            repo_state = RepoState(self.repo_path)
            # Just save the manifest to update modification time
            repo_state.save_manifest()
            logger.info(f"✅ Updated repo state for {len(chunks)} chunks")
        except Exception as e:
            # Non-critical - log and continue
            logger.warning(f"⚠️ Could not update repo state: {e}")
