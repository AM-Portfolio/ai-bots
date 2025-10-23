"""
Embedding Pipeline - Simplified Orchestrator

This module coordinates the embedding generation workflow by using specialized modules:
- pipeline.file_discovery: File discovery and filtering
- pipeline.code_parser: Code parsing and chunking
- pipeline.batch_embedder: Batch embedding generation
- enhanced_summarizer: Code summarization

The pipeline orchestrates these modules to generate embeddings from code.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.rate_limiter import RateLimitController
from storage.repo_state import RepoState
from utils.change_planner import ChangePlanner
from enhanced_summarizer import EnhancedCodeSummarizer

# Import shared embedding service
from shared.vector_db.embedding_service import EmbeddingService

# Import pipeline modules
from pipeline.file_discovery import FileDiscovery
from pipeline.code_parser import CodeParser
from pipeline.batch_embedder import BatchEmbeddingGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose Azure and HTTP logs - only show errors
logging.getLogger('shared.azure_services.model_deployment_service').setLevel(logging.ERROR)
logging.getLogger('shared.azure_services').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db.embedding_service').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db').setLevel(logging.WARNING)


class EmbeddingPipeline:
    """
    Simplified embedding pipeline orchestrator.
    
    Delegates to specialized modules:
    - FileDiscovery: Finds code files
    - CodeParser: Parses and chunks code
    - BatchEmbeddingGenerator: Generates embeddings
    - EnhancedCodeSummarizer: Generates summaries
    
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
        
        logger.info("🚀 Initializing Embedding Pipeline...")
        
        # Initialize core components
        self.rate_limiter = RateLimitController()
        self.repo_state = RepoState(manifest_path)
        self.change_planner = ChangePlanner(repo_path)
        self.summarizer = EnhancedCodeSummarizer(self.repo_state, self.rate_limiter)
        
        # Initialize embedding service
        logger.info(f"📦 Initializing embedding service (provider: {embedding_provider})...")
        self.embedding_service = EmbeddingService(provider=embedding_provider)
        embedding_dim = self.embedding_service.get_dimension()
        logger.info(f"   Embedding dimension: {embedding_dim}")
        
        # Initialize pipeline modules
        self.file_discovery = FileDiscovery(self.repo_path)
        self.code_parser = CodeParser(self.repo_path)
        self.batch_embedder = BatchEmbeddingGenerator(
            self.embedding_service,
            self.rate_limiter
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
    
    
    async def generate_embeddings(
        self,
        max_files: Optional[int] = None,
        force_reindex: bool = False,
        file_filter: Optional[Set[str]] = None,
        file_contents: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for code files using modular pipeline.
        
        Workflow:
        1. FileDiscovery: Discover and filter files
        2. CodeParser: Parse and chunk files
        3. EnhancedCodeSummarizer: Generate summaries
        4. BatchEmbeddingGenerator: Generate embeddings
        
        Args:
            max_files: Limit number of files to process (None = all)
            force_reindex: Force re-embedding of all files
            file_filter: Optional set of file paths to filter (from GitHub LLM)
            file_contents: Optional dict of file path -> content (from GitHub API)
            
        Returns:
            Dict with:
            - embedding_data: List of dicts with chunk info and embeddings
            - stats: Statistics
            - files_processed: List of processed files
        """
        logger.info("="* 60)
        logger.info("🎯 Starting Embedding Pipeline")
        logger.info("=" * 60)
        
        # Verify embedding service
        logger.info("🔌 Verifying embedding service...")
        if not await self._verify_embedding_service():
            raise Exception("Embedding service not available. Please check configuration.")
        
        # Start rate limiter
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
            
            # Step 1: Discover files using FileDiscovery module
            logger.info("\n📁 Step 1: File Discovery")
            if file_filter:
                # When using GitHub file filter, use those paths directly
                logger.info(f"📡 Using GitHub repository files: {len(file_filter)} files")
                all_files = list(file_filter)
                stats["files_discovered"] = len(all_files)
            else:
                # Local file discovery
                all_files = self.file_discovery.discover_files()
                stats["files_discovered"] = len(all_files)
            
            # Step 2: Filter files
            logger.info("\n🎯 Step 2: File Filtering")
            if file_filter:
                # Use provided file filter from GitHub LLM
                logger.info(f"🔍 Using GitHub analysis results: {len(file_filter)} files")
                # For GitHub repos, all_files is already the filtered set
                prioritized_files = self.file_discovery.apply_limit(all_files, max_files)
                logger.info(f"📊 Processing {len(prioritized_files)} files from GitHub repository")
            else:
                # Use change detection for local files
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
            
            # Step 3: Parse and chunk using CodeParser module
            logger.info("\n📖 Step 3: Parsing and Chunking")
            all_chunks = self.code_parser.parse_files(
                prioritized_files,
                file_contents=file_contents
            )
            stats["chunks_generated"] = len(all_chunks)
            
            # Show chunk type distribution
            chunk_types = {}
            for chunk in all_chunks:
                chunk_type = chunk.metadata.chunk_type
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            if chunk_types:
                logger.info(f"   Chunk types: {dict(sorted(chunk_types.items(), key=lambda x: x[1], reverse=True))}")
            
            # Step 4: Summarize chunks
            logger.info("\n📝 Step 4: Generating Summaries")
            logger.info(f"   Processing {len(all_chunks)} chunks with AI summarization")
            summaries = await self.summarizer.summarize_batch(all_chunks)
            
            # Log summarization stats
            summary_lengths = [len(s) for s in summaries.values() if s]
            if summary_lengths:
                avg_length = sum(summary_lengths) / len(summary_lengths)
                logger.info(f"   ✅ Generated {len(summaries)} summaries (avg length: {avg_length:.0f} chars)")
            
            # Step 5: Generate embeddings using BatchEmbeddingGenerator module
            logger.info("\n🔢 Step 5: Generating Embeddings")
            embedding_data = await self.batch_embedder.generate_batch(all_chunks, summaries)
            
            stats["chunks_embedded"] = len(embedding_data)
            stats["failed_chunks"] = len(all_chunks) - len(embedding_data)
            stats["success_rate"] = (len(embedding_data) / len(all_chunks) * 100) if all_chunks else 0
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ Embedding Generation Complete!")
            logger.info(f"📊 Generated: {len(embedding_data)}/{len(all_chunks)} embeddings")
            logger.info(f"📈 Success Rate: {stats['success_rate']:.1f}%")
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
            
        finally:
            await self.rate_limiter.stop()

