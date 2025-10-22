"""
Main Orchestrator for Code Intelligence Embedding Pipeline

Two-Phase Approach:
1. Phase 1: Parse → Summarize (with caching)
2. Phase 2: Embed code + summaries → Store in Qdrant

Features:
- Incremental updates (only embed changed files)
- Rate-limit aware with adaptive batching
- Smart prioritization (changed files first)
- Resilient error handling with DLQ
- Progress tracking and reporting
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from code_intelligence.rate_limiter import RateLimitController, QuotaType
from code_intelligence.repo_state import RepoState
from code_intelligence.parsers import parser_registry
from code_intelligence.change_planner import ChangePlanner
from code_intelligence.summarizer import CodeSummarizer
from code_intelligence.vector_store import VectorStore, EmbeddingPoint

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingOrchestrator:
    """
    Main orchestrator for the embedding pipeline.
    
    Coordinates all stages:
    1. File discovery and change detection
    2. Prioritization
    3. Parsing and chunking
    4. Summarization (Phase 1)
    5. Embedding (Phase 2)
    6. Vector DB storage
    """
    
    def __init__(
        self,
        repo_path: str = ".",
        manifest_path: str = ".code-intelligence-state.json",
        collection_name: str = "code_intelligence",
        qdrant_path: str = "./qdrant_data",
        embedding_model: str = "text-embedding-3-large"
    ):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository
            manifest_path: Path to state manifest
            collection_name: Qdrant collection name
            qdrant_path: Path to Qdrant storage
            embedding_model: Azure OpenAI embedding model
        """
        self.repo_path = Path(repo_path)
        self.embedding_model = embedding_model
        
        # Initialize components
        logger.info("🚀 Initializing Code Intelligence Pipeline...")
        
        self.rate_limiter = RateLimitController()
        self.repo_state = RepoState(manifest_path)
        self.change_planner = ChangePlanner(repo_path)
        self.summarizer = CodeSummarizer(self.repo_state, self.rate_limiter)
        self.vector_store = VectorStore(
            collection_name=collection_name,
            qdrant_path=qdrant_path
        )
        
        # Initialize Azure OpenAI for embeddings
        self.embedding_client = None
        self._init_embedding_client()
        
        logger.info("✅ Pipeline initialized")
    
    def _init_embedding_client(self):
        """Initialize Azure OpenAI embedding client"""
        try:
            from shared.azure_services.azure_ai_manager import azure_ai_manager
            if azure_ai_manager.models.is_available():
                self.embedding_client = azure_ai_manager.models
                logger.info("✅ Using Azure OpenAI for embeddings")
            else:
                logger.error("❌ Azure OpenAI not configured!")
        except Exception as e:
            logger.error(f"Failed to initialize embedding client: {e}")
    
    def discover_files(
        self,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """
        Discover all code files in repository.
        
        Args:
            exclude_patterns: Patterns to exclude (e.g., ['node_modules', '.git'])
            
        Returns:
            List of file paths
        """
        if exclude_patterns is None:
            exclude_patterns = [
                '.git', 'node_modules', '__pycache__', 'venv',
                '.venv', 'dist', 'build', '.next', '.nuxt',
                'target', 'out', '.idea', '.vscode'
            ]
        
        files = []
        supported_extensions = parser_registry.get_supported_extensions()
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_patterns]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Check if supported
                if file_path.suffix.lower() in supported_extensions:
                    files.append(str(file_path.relative_to(self.repo_path)))
        
        logger.info(f"📁 Discovered {len(files)} code files")
        return files
    
    async def run_incremental(
        self,
        max_files: Optional[int] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Run incremental embedding (only changed files).
        
        Args:
            max_files: Limit number of files to process (None = all)
            force_reindex: Force re-embedding of all files
            
        Returns:
            Stats about the run
        """
        logger.info("="* 60)
        logger.info("🎯 Starting Incremental Embedding Pipeline")
        logger.info("=" * 60)
        
        # Start rate limiter workers
        await self.rate_limiter.start()
        
        try:
            # Step 1: Discover files
            all_files = self.discover_files()
            
            # Step 2: Detect changed files
            if force_reindex:
                logger.info("🔄 Force reindex enabled - processing all files")
                changed_files = set(all_files)
            else:
                changed_files = self.repo_state.get_changed_files(all_files)
            
            # Step 3: Prioritize files
            prioritized_files = self.change_planner.get_top_priority_files(
                all_files,
                max_files=max_files or len(all_files),
                changed_files=changed_files
            )
            
            logger.info(
                f"📊 Processing {len(prioritized_files)} files "
                f"({len(changed_files)} changed)"
            )
            
            # Step 4: Parse and chunk
            logger.info("📖 Phase 1: Parsing and Summarization")
            all_chunks = []
            for file_path in tqdm(prioritized_files, desc="Parsing files"):
                try:
                    chunks = parser_registry.parse_file(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Failed to parse {file_path}: {e}")
            
            logger.info(f"✂️ Generated {len(all_chunks)} code chunks")
            
            # Step 5: Summarize chunks (Phase 1)
            logger.info("📝 Generating summaries...")
            summaries = await self.summarizer.summarize_batch(all_chunks)
            
            # Step 6: Generate embeddings (Phase 2)
            logger.info("🔢 Phase 2: Embedding Generation")
            embeddings = await self._embed_batch(all_chunks, summaries)
            
            # Step 7: Store in Qdrant
            logger.info("💾 Storing embeddings in Qdrant...")
            embedding_points = [
                EmbeddingPoint(
                    chunk_id=chunk.chunk_id,
                    embedding=embeddings[i],
                    content=chunk.content,
                    summary=summaries.get(chunk.chunk_id, ""),
                    metadata={
                        "file_path": chunk.metadata.file_path,
                        "language": chunk.metadata.language,
                        "chunk_type": chunk.metadata.chunk_type,
                        "symbol_name": chunk.metadata.symbol_name,
                        "start_line": chunk.metadata.start_line,
                        "end_line": chunk.metadata.end_line,
                        "token_count": chunk.metadata.token_count
                    }
                )
                for i, chunk in enumerate(all_chunks)
                if i < len(embeddings)
            ]
            
            upsert_result = await self.vector_store.upsert_batch(embedding_points)
            
            # Step 8: Update repo state
            for file_path in prioritized_files:
                file_chunks = [c for c in all_chunks if c.metadata.file_path == file_path]
                self.repo_state.update_file_state(
                    file_path=file_path,
                    language=file_chunks[0].metadata.language if file_chunks else None,
                    chunk_count=len(file_chunks),
                    status="completed"
                )
            
            self.repo_state.save_manifest()
            
            # Step 9: Generate report
            stats = {
                "files_discovered": len(all_files),
                "files_changed": len(changed_files),
                "files_processed": len(prioritized_files),
                "chunks_generated": len(all_chunks),
                "chunks_embedded": upsert_result["successful"],
                "chunks_failed": upsert_result["failed"],
                "success_rate": upsert_result["success_rate"],
                "rate_limiter_stats": {
                    quota.value: self.rate_limiter.get_metrics(quota)
                    for quota in QuotaType
                }
            }
            
            logger.info("=" * 60)
            logger.info("✅ Pipeline Complete!")
            logger.info(f"📊 Processed: {stats['chunks_embedded']}/{stats['chunks_generated']} chunks")
            logger.info(f"📈 Success Rate: {stats['success_rate']:.1f}%")
            logger.info("=" * 60)
            
            return stats
            
        finally:
            await self.rate_limiter.stop()
    
    async def _embed_batch(
        self,
        chunks: List,
        summaries: Dict[str, str]
    ) -> List[List[float]]:
        """
        Generate embeddings for chunks with summaries.
        
        Args:
            chunks: List of code chunks
            summaries: Dict of chunk_id -> summary
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        batch_size = self.rate_limiter.get_adaptive_batch_size(QuotaType.EMBEDDING)
        
        logger.info(f"Embedding {len(chunks)} chunks in batches of {batch_size}")
        
        for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding"):
            batch = chunks[i:i + batch_size]
            
            # Prepare texts (code + summary)
            texts = [
                f"{summaries.get(chunk.chunk_id, '')}\n\n{chunk.content[:2000]}"
                for chunk in batch
            ]
            
            # Embed with rate limiting
            async def embed_batch():
                if not self.embedding_client:
                    raise Exception("Embedding client not initialized")
                
                response = await self.embedding_client.create_embeddings(
                    texts=texts,
                    model=self.embedding_model
                )
                return [item["embedding"] for item in response]
            
            try:
                batch_embeddings = await self.rate_limiter.submit(
                    QuotaType.EMBEDDING,
                    embed_batch,
                    priority=2
                )
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to embed batch {i//batch_size + 1}: {e}")
                # Add placeholder embeddings for failed batch
                embeddings.extend([[0.0] * 3072] * len(batch))
        
        return embeddings


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Intelligence Embedding Pipeline")
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to repository"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of files to process"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-embedding of all files"
    )
    parser.add_argument(
        "--collection",
        default="code_intelligence",
        help="Qdrant collection name"
    )
    
    args = parser.parse_args()
    
    orchestrator = EmbeddingOrchestrator(
        repo_path=args.repo,
        collection_name=args.collection
    )
    
    stats = await orchestrator.run_incremental(
        max_files=args.max_files,
        force_reindex=args.force
    )
    
    print("\n📊 Final Statistics:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Chunks embedded: {stats['chunks_embedded']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
