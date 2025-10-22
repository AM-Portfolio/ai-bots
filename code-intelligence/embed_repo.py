"""
Embedding Pipeline - Pure Embedding Logic

Responsibilities:
- File discovery and filtering
- Parsing and chunking code
- Enhanced summarization
- Batch embedding generation

Does NOT handle:
- Vector DB operations (done in orchestrator)
- GitHub LLM analysis (done in orchestrator)
- API requests (done in API layer)
- CLI commands (done in orchestrator)

This module focuses purely on generating embeddings from code.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from rate_limiter import RateLimitController, QuotaType
from repo_state import RepoState
from parsers import parser_registry
from change_planner import ChangePlanner
from enhanced_summarizer import EnhancedCodeSummarizer

# Import shared embedding service from vector_db module
from shared.vector_db.embedding_service import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Pure embedding pipeline - generates embeddings from code.
    
    Stages:
    1. File discovery and filtering
    2. Parsing and chunking
    3. Enhanced summarization
    4. Batch embedding generation
    
    Returns structured data ready for vector DB storage.
    """
    
    def __init__(
        self,
        repo_path: str = ".",
        manifest_path: str = ".code-intelligence-state.json",
        embedding_provider: str = "auto"
    ):
        """
        Initialize embedding pipeline.
        
        Args:
            repo_path: Path to repository
            manifest_path: Path to state manifest
            embedding_provider: Embedding provider ('auto', 'azure', 'together')
        """
        self.repo_path = Path(repo_path)
        
        # Initialize components
        logger.info("🚀 Initializing Embedding Pipeline...")
        
        self.rate_limiter = RateLimitController()
        self.repo_state = RepoState(manifest_path)
        self.change_planner = ChangePlanner(repo_path)
        self.summarizer = EnhancedCodeSummarizer(self.repo_state, self.rate_limiter)
        
        # Initialize shared embedding service (uses config from settings)
        logger.info(f"📦 Initializing embedding service (provider: {embedding_provider})...")
        self.embedding_service = EmbeddingService(provider=embedding_provider)
        
        # Get dimension from embedding service
        embedding_dim = self.embedding_service.get_dimension()
        logger.info(f"   Embedding dimension: {embedding_dim}")
        
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
    
    async def generate_embeddings(
        self,
        max_files: Optional[int] = None,
        force_reindex: bool = False,
        file_filter: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for code files.
        
        Workflow:
        1. Discover local files
        2. Filter by file_filter (if provided) or change detection
        3. Parse and chunk
        4. Summarize
        5. Generate embeddings
        
        Args:
            max_files: Limit number of files to process (None = all)
            force_reindex: Force re-embedding of all files
            file_filter: Optional set of file paths to filter (from GitHub LLM)
            
        Returns:
            Dict with:
            - embedding_data: List of dicts with chunk info and embeddings
            - stats: Statistics
            - files_processed: List of processed files
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
            stats = {
                "success": True,
                "files_discovered": 0,
                "files_processed": 0,
                "chunks_generated": 0,
                "chunks_embedded": 0,
                "failed_chunks": 0,
                "success_rate": 0.0
            }
            
            # Step 1: Discover files
            all_files = self.discover_files()
            stats["files_discovered"] = len(all_files)
            
            # Step 2: Filter files
            if file_filter and not force_reindex:
                # Use provided file filter (e.g., from GitHub LLM)
                logger.info(f"🎯 Filtering files using provided filter ({len(file_filter)} files)")
                prioritized_files = []
                
                for file_path in all_files:
                    # Check if file_path matches any filter path
                    if any(filter_path in file_path for filter_path in file_filter):
                        prioritized_files.append(file_path)
                
                logger.info(f"   Filtered to {len(prioritized_files)} files")
                
                if max_files and len(prioritized_files) > max_files:
                    prioritized_files = prioritized_files[:max_files]
                    logger.info(f"   Limited to {max_files} files")
            else:
                # Normal prioritization using change detection
                if force_reindex:
                    logger.info("🔄 Force reindex enabled - processing all files")
                    changed_files = set(all_files)
                else:
                    changed_files = self.repo_state.get_changed_files(all_files)
                
                prioritized_files = self.change_planner.get_top_priority_files(
                    all_files,
                    max_files=max_files or len(all_files),
                    changed_files=changed_files
                )
                
                logger.info(
                    f"📊 Processing {len(prioritized_files)} files "
                    f"({len(changed_files)} changed)"
                )
            
            stats["files_processed"] = len(prioritized_files)
            
            # Step 3: Parse and chunk
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
            
            stats["chunks_generated"] = len(all_chunks)
            
            # Show chunk type distribution
            chunk_types = {}
            for chunk in all_chunks:
                chunk_type = chunk.metadata.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            logger.info(f"   Chunk types: {dict(sorted(chunk_types.items(), key=lambda x: x[1], reverse=True))}")
            
            # Step 4: Summarize chunks
            logger.info("📝 Generating enhanced summaries...")
            logger.info(f"   Processing {len(all_chunks)} chunks with AI summarization")
            summaries = await self.summarizer.summarize_batch(all_chunks)
            
            # Log summarization stats
            summary_lengths = [len(s) for s in summaries.values() if s]
            if summary_lengths:
                avg_length = sum(summary_lengths) / len(summary_lengths)
                logger.info(f"   ✅ Generated {len(summaries)} summaries (avg length: {avg_length:.0f} chars)")
            
            # Step 5: Generate embeddings
            logger.info("🔢 Generating embeddings...")
            logger.info(f"   Processing {len(all_chunks)} chunks in batches")
            embedding_data = await self._generate_embeddings_batch(all_chunks, summaries)
            
            stats["chunks_embedded"] = len(embedding_data)
            stats["failed_chunks"] = len(all_chunks) - len(embedding_data)
            stats["success_rate"] = (len(embedding_data) / len(all_chunks) * 100) if all_chunks else 0
            
            logger.info("=" * 60)
            logger.info("✅ Embedding Generation Complete!")
            logger.info(f"📊 Generated: {len(embedding_data)}/{len(all_chunks)} embeddings")
            logger.info("=" * 60)
            
            # Return embedding data for orchestrator to store
            return {
                "success": True,
                "embedding_data": embedding_data,
                "chunks": all_chunks,
                "summaries": summaries,
                "prioritized_files": prioritized_files,
                "stats": stats
            }
            logger.info("✅ Pipeline Complete!")
            logger.info(f"📊 Processed: {stats['chunks_embedded']}/{stats['chunks_generated']} chunks")
            if stats.get("github_analysis"):
                logger.info(f"🔍 GitHub: {stats['github_analysis']['files_found']} files, confidence: {stats['github_analysis']['confidence']:.2f}")
            logger.info(f"📈 Success Rate: {stats['success_rate']:.1f}%")
            logger.info("=" * 60)
            
            return stats
            
        finally:
            await self.rate_limiter.stop()
    
    async def _generate_embeddings_batch(
        self,
        chunks: List,
        summaries: Dict[str, str]
    ) -> List[Dict]:
        """
        Generate embeddings in small batches WITHOUT storing them.
        Returns embedding data for the orchestrator to handle storage.
        
        Args:
            chunks: List of code chunks
            summaries: Dict of chunk_id -> summary
            
        Returns:
            List of dicts containing embedding data with structure:
            {
                "chunk_id": str,
                "embedding": List[float],
                "content": str,
                "summary": str,
                "metadata": dict
            }
        """
        batch_size = self.rate_limiter.get_adaptive_batch_size(QuotaType.EMBEDDING)
        # Keep batch size reasonable (max 50 at a time)
        batch_size = min(batch_size, 50)
        
        total_chunks = len(chunks)
        embedding_data = []
        num_batches = (total_chunks + batch_size - 1) // batch_size
        
        logger.info(f"   Batch size: {batch_size} chunks")
        logger.info(f"   Total batches: {num_batches}")
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_chunks)
            batch = chunks[start_idx:end_idx]
            
            # Calculate progress
            progress = ((batch_num + 1) / num_batches) * 100
            
            logger.info(f"\n📦 Batch {batch_num + 1}/{num_batches} ({progress:.1f}% complete)")
            logger.info(f"   Processing chunks {start_idx + 1}-{end_idx} of {total_chunks}")
            
            # Prepare texts (summary + code)
            texts = [
                f"{summaries.get(chunk.chunk_id, '')}\n\n{chunk.content[:2000]}"
                for chunk in batch
            ]
            
            # Embed with rate limiting using shared embedding service
            async def embed_batch():
                return await self.embedding_service.generate_embeddings_batch(texts)
            
            try:
                # Generate embeddings
                logger.debug(f"   🔢 Generating embeddings...")
                batch_embeddings = await self.rate_limiter.submit(
                    QuotaType.EMBEDDING,
                    embed_batch,
                    priority=2
                )
                
                # Create embedding data structures (no storage)
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
                
                logger.info(f"   ✅ Batch complete: {len(batch_embeddings)} embeddings generated")
                logger.info(f"   📊 Total progress: {len(embedding_data)}/{total_chunks} chunks ({(len(embedding_data)/total_chunks)*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"   ❌ Batch {batch_num + 1} failed: {e}")
                # Continue with next batch even if this one fails
        
        logger.info(f"\n✅ Embedding generation complete: {len(embedding_data)} embeddings generated")
        return embedding_data


async def main():
    """
    Main entry point for standalone embedding pipeline execution.
    Note: For production use, call this through orchestrator.py instead.
    """
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
    
    args = parser.parse_args()
    
    # Create pipeline (no collection needed - that's orchestrator's job)
    pipeline = EmbeddingPipeline(
        repo_path=args.repo
    )
    
    # Generate embeddings (returns data, doesn't store)
    result = await pipeline.generate_embeddings(
        file_filter=None,  # Process all files
        max_files=args.max_files,
        force_reindex=args.force
    )
    
    print("\n📊 Embedding Generation Results:")
    print(f"  Files processed: {result['stats']['files_processed']}")
    print(f"  Chunks generated: {len(result['embedding_data'])}")
    print(f"  Success rate: {result['stats']['success_rate']:.1f}%")
    print("\n⚠️  Note: Embeddings generated but NOT stored.")
    print("   Use orchestrator.py to store embeddings in vector DB.")


if __name__ == "__main__":
    asyncio.run(main())
