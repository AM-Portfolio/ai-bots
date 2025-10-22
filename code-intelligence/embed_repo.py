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

from rate_limiter import RateLimitController, QuotaType
from repo_state import RepoState
from parsers import parser_registry
from change_planner import ChangePlanner
from enhanced_summarizer import EnhancedCodeSummarizer
from vector_store import VectorStore, EmbeddingPoint

# Import shared embedding service from vector_db module
from shared.vector_db.embedding_service import EmbeddingService

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
        embedding_provider: str = "auto"
    ):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository
            manifest_path: Path to state manifest
            collection_name: Qdrant collection name
            qdrant_path: Path to Qdrant storage
            embedding_provider: Embedding provider ('auto', 'azure', 'together')
        """
        self.repo_path = Path(repo_path)
        
        # Initialize components
        logger.info("🚀 Initializing Code Intelligence Pipeline...")
        
        self.rate_limiter = RateLimitController()
        self.repo_state = RepoState(manifest_path)
        self.change_planner = ChangePlanner(repo_path)
        self.summarizer = EnhancedCodeSummarizer(self.repo_state, self.rate_limiter)
        
        # Initialize shared embedding service (uses config from settings)
        logger.info(f"📦 Initializing embedding service (provider: {embedding_provider})...")
        self.embedding_service = EmbeddingService(provider=embedding_provider)
        
        # Get dimension from embedding service for vector store
        embedding_dim = self.embedding_service.get_dimension()
        logger.info(f"   Embedding dimension: {embedding_dim}")
        
        self.vector_store = VectorStore(
            collection_name=collection_name,
            qdrant_path=qdrant_path,
            embedding_dim=embedding_dim
        )
        
        logger.info("✅ Pipeline initialized")
    
    async def _verify_embedding_service(self):
        """Verify embedding service is connected"""
        try:
            health_status = await self.embedding_service.health_check()
            if health_status.get('connected', False):
                logger.info("✅ Embedding service connected and healthy")
                logger.info(f"   Provider: {health_status.get('provider')}")
                logger.info(f"   Model: {health_status.get('model')}")
                return True
            else:
                logger.error(f"❌ Embedding service not connected: {health_status.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            logger.error(f"Failed to verify embedding service: {e}")
            return False
    
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
                # Version control
                '.git', '.svn', '.hg',
                # Dependencies
                'node_modules', 'bower_components', 'vendor', 'packages',
                # Python
                '__pycache__', 'venv', '.venv', 'env', '.env', 'virtualenv',
                '.pytest_cache', '.mypy_cache', '.tox', 'eggs', '.eggs',
                # Build outputs
                'dist', 'build', 'out', 'target', 'bin', 'obj',
                # Framework specific
                '.next', '.nuxt', '.cache', '.parcel-cache',
                # IDE
                '.idea', '.vscode', '.vs', '.eclipse', '.project',
                # Test/Coverage
                'coverage', 'htmlcov', '.coverage', '.nyc_output',
                # Logs
                'logs', 'log',
                # Other
                'tmp', 'temp', '.tmp'
            ]
        
        # File patterns to skip
        skip_file_patterns = [
            'test_', '_test.', '.test.', '.spec.',  # Test files
            '.min.', '-min.',  # Minified files
            'bundle.', 'chunk.',  # Bundled files
        ]
        
        # Exact filenames to skip
        skip_filenames = {
            'package-lock.json', 'yarn.lock', 'poetry.lock',
            'Pipfile.lock', 'pnpm-lock.yaml', 'bun.lockb'
        }
        
        files = []
        skipped_dirs = 0
        skipped_files = 0
        supported_extensions = parser_registry.get_supported_extensions()
        
        logger.info("🔍 Starting file discovery...")
        logger.info(f"   Excluding directories: {', '.join(exclude_patterns[:10])}...")
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out excluded directories
            original_dir_count = len(dirs)
            dirs[:] = [d for d in dirs if d not in exclude_patterns]
            skipped_dirs += (original_dir_count - len(dirs))
            
            for filename in filenames:
                # Skip exact filenames
                if filename in skip_filenames:
                    skipped_files += 1
                    continue
                
                # Skip file patterns
                if any(pattern in filename.lower() for pattern in skip_file_patterns):
                    skipped_files += 1
                    continue
                
                file_path = Path(root) / filename
                
                # Check if supported extension
                if file_path.suffix.lower() in supported_extensions:
                    files.append(str(file_path.relative_to(self.repo_path)))
        
        logger.info(f"📁 Discovered {len(files)} code files")
        logger.info(f"   Skipped {skipped_dirs} directories, {skipped_files} files")
        logger.info(f"   Supported extensions: {', '.join(list(supported_extensions)[:10])}...")
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
        
        # Verify embedding service is connected
        logger.info("🔌 Verifying embedding service...")
        if not await self._verify_embedding_service():
            raise Exception("Embedding service not available. Please check configuration.")
        
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
            parse_errors = []
            
            for file_path in tqdm(prioritized_files, desc="Parsing files"):
                try:
                    chunks = parser_registry.parse_file(file_path)
                    all_chunks.extend(chunks)
                    if len(chunks) > 0:
                        logger.debug(f"   ✓ {file_path}: {len(chunks)} chunks")
                except Exception as e:
                    logger.error(f"   ✗ Failed to parse {file_path}: {e}")
                    parse_errors.append((file_path, str(e)))
            
            logger.info(f"✂️ Generated {len(all_chunks)} code chunks from {len(prioritized_files)} files")
            if parse_errors:
                logger.warning(f"   ⚠️  {len(parse_errors)} files failed to parse")
            
            # Show chunk type distribution
            chunk_types = {}
            for chunk in all_chunks:
                chunk_type = chunk.metadata.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            logger.info(f"   Chunk types: {dict(sorted(chunk_types.items(), key=lambda x: x[1], reverse=True))}")
            
            # Step 5: Summarize chunks (Phase 1)
            logger.info("📝 Generating enhanced summaries...")
            logger.info(f"   Processing {len(all_chunks)} chunks with AI summarization")
            summaries = await self.summarizer.summarize_batch(all_chunks)
            
            # Log summarization stats
            summary_lengths = [len(s) for s in summaries.values() if s]
            if summary_lengths:
                avg_length = sum(summary_lengths) / len(summary_lengths)
                logger.info(f"   ✅ Generated {len(summaries)} summaries (avg length: {avg_length:.0f} chars)")
            
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
        Generate embeddings for chunks with summaries using shared embedding service.
        
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
            
            # Prepare texts (summary + code)
            texts = [
                f"{summaries.get(chunk.chunk_id, '')}\n\n{chunk.content[:2000]}"
                for chunk in batch
            ]
            
            # Embed with rate limiting using shared embedding service
            async def embed_batch():
                # Use shared embedding service (handles Azure, Together AI, fallback)
                return await self.embedding_service.generate_embeddings_batch(texts)
            
            try:
                batch_embeddings = await self.rate_limiter.submit(
                    QuotaType.EMBEDDING,
                    embed_batch,
                    priority=2
                )
                embeddings.extend(batch_embeddings)
                logger.debug(f"✅ Batch {i//batch_size + 1} embedded: {len(batch_embeddings)} vectors")
            except Exception as e:
                logger.error(f"Failed to embed batch {i//batch_size + 1}: {e}")
                # Add placeholder embeddings for failed batch (use configured dimension)
                placeholder_dim = self.embedding_service.get_dimension()
                embeddings.extend([[0.0] * placeholder_dim] * len(batch))
        
        return embeddings
        
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
