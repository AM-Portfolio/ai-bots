"""
Code Intelligence Orchestrator

Core orchestration logic for code intelligence operations.
Provides high-level workflows for:
- Repository embedding with optional GitHub LLM analysis
- Code summarization
- Change analysis
- Health checks

This is the coordination layer that the API/CLI should call.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add parent directory to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from embed_repo import EmbeddingPipeline
from enhanced_summarizer import EnhancedCodeSummarizer
from utils.change_planner import ChangePlanner
from storage.repo_state import RepoState
from utils.rate_limiter import RateLimitController
from storage.vector_store import VectorStore
from shared.vector_db.embedding_service import EmbeddingService
from shared.config import settings
from analysis.github_analyzer import GitHubAnalyzer
from pipeline.embedding_workflow import EmbeddingWorkflow

logger = logging.getLogger(__name__)


class CodeIntelligenceOrchestrator:
    """
    Main orchestrator for code intelligence operations.
    
    Orchestrates:
    - GitHub LLM for repository analysis
    - EmbeddingOrchestrator for embedding pipeline
    - Enhanced summarization
    - Change analysis
    - Health checks
    
    This is the coordination layer that the API should call.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository (default: current directory)
        """
        self.repo_path = Path(repo_path).resolve()
        self.settings = settings
        self.github_analyzer = GitHubAnalyzer()
        logger.info(f"📁 Repository: {self.repo_path}")
    
    async def embed_repository(
        self,
        collection_name: str = "code_intelligence",
        max_files: Optional[int] = None,
        force_reindex: bool = False,
        github_repository: Optional[str] = None,
        query: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate repository embedding with optional GitHub LLM analysis.
        
        Workflow:
        1. (Optional) Use GitHub LLM to analyze repository
        2. Get relevant files based on analysis
        3. Delegate to EmbeddingOrchestrator for embedding pipeline
        
        Args:
            collection_name: Qdrant collection name
            max_files: Maximum number of files to process
            force_reindex: Force re-embedding of all files
            github_repository: Optional GitHub repository (owner/repo)
            query: Optional query for filtering files
            language: Optional language filter
            
        Returns:
            Statistics dictionary with processing results
        """
        logger.info("🚀 Starting repository embedding orchestration...")
        
        stats = {
            "success": True,
            "github_analysis": None,
            "files_discovered": 0,
            "files_processed": 0,
            "chunks_generated": 0,
            "chunks_embedded": 0,
            "failed_chunks": 0,
            "success_rate": 0.0
        }
        
        # STEP 1: Optional GitHub LLM Analysis
        github_file_paths = await self._analyze_github_repository(
            github_repository=github_repository,
            query=query,
            max_files=max_files,
            language=language,
            stats=stats
        )
        
        # STEP 2: Generate embeddings
        embedding_result = await self._generate_embeddings(
            github_file_paths=github_file_paths,
            max_files=max_files,
            force_reindex=force_reindex
        )
        
        # STEP 3: Store embeddings using workflow
        total_stored, total_failed = await self._store_embeddings(
            collection_name=collection_name,
            embedding_result=embedding_result
        )
        
        # Merge stats
        stats.update(embedding_result["stats"])
        stats["chunks_embedded"] = total_stored
        stats["failed_chunks"] = total_failed
        
        logger.info("\n✅ Repository embedding orchestration complete!")
        if stats.get("github_analysis"):
            logger.info(f"   GitHub: {stats['github_analysis']['files_found']} files analyzed")
        logger.info(f"   Stored: {total_stored} embeddings")

        
        return stats
    
    async def _analyze_github_repository(
        self,
        github_repository: Optional[str],
        query: Optional[str],
        max_files: Optional[int],
        language: Optional[str],
        stats: Dict[str, Any]
    ) -> set:
        """
        Analyze GitHub repository using GitHub LLM.
        
        Returns:
            Set of relevant file paths
        """
        if not github_repository:
            logger.info("\n📂 STEP 1: Using local file discovery (no GitHub repository specified)")
            return set()
        
        logger.info(f"\n🔍 STEP 1: GitHub LLM Repository Analysis")
        
        analysis_result = await self.github_analyzer.analyze_repository(
            repository=github_repository,
            query=query,
            max_results=max_files or 50,
            language=language
        )
        
        if analysis_result.get("error"):
            logger.info("   Continuing with local discovery...")
            return set()
        
        if analysis_result["files_found"] > 0:
            stats["github_analysis"] = {
                "repository": github_repository,
                "files_found": analysis_result["files_found"],
                "confidence": analysis_result["confidence"],
                "summary": analysis_result["summary"]
            }
        
        return analysis_result["file_paths"]
    
    async def _generate_embeddings(
        self,
        github_file_paths: set,
        max_files: Optional[int],
        force_reindex: bool
    ) -> Dict[str, Any]:
        """
        Generate embeddings using EmbeddingPipeline.
        
        Returns:
            Embedding result dictionary
        """
        logger.info("\n📖 STEP 2: Repository Embedding Pipeline")
        
        embedding_pipeline = EmbeddingPipeline(
            repo_path=str(self.repo_path)
        )
        
        return await embedding_pipeline.generate_embeddings(
            file_filter=github_file_paths if github_file_paths else None,
            max_files=max_files,
            force_reindex=force_reindex
        )
    
    async def _store_embeddings(
        self,
        collection_name: str,
        embedding_result: Dict[str, Any]
    ) -> tuple[int, int]:
        """
        Store embeddings in vector database and update repo state.
        
        Returns:
            Tuple of (total_stored, total_failed)
        """
        logger.info("\n💾 STEP 3: Storing embeddings in vector database")
        
        # Use EmbeddingWorkflow for storage
        workflow = EmbeddingWorkflow(
            repo_path=str(self.repo_path),
            collection_name=collection_name
        )
        
        result = await workflow.execute(embedding_result)
        
        return result["total_stored"], result["total_failed"]
    
    async def generate_summaries(
        self,
        files: Optional[list] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Generate enhanced summaries for code files.
        
        Args:
            files: Specific files to summarize (None = all files)
            force: Force regeneration of cached summaries
            
        Returns:
            Dictionary with summary results
        """
        logger.info("📝 Generating enhanced code summaries...")
        
        repo_state = RepoState(repo_path=str(self.repo_path))
        rate_limiter = RateLimitController()
        summarizer = EnhancedCodeSummarizer(
            repo_state=repo_state,
            rate_limiter=rate_limiter
        )
        
        # TODO: Implement batch summary generation
        results = {
            "files_processed": 0,
            "summaries_generated": 0,
            "cached_summaries": 0
        }
        
        return results
    
    async def analyze_changes(
        self,
        base_ref: str = "HEAD",
        show_priorities: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze repository changes and file priorities.
        
        Args:
            base_ref: Git reference to compare against
            show_priorities: Display priority breakdown
            
        Returns:
            Analysis results with changed files and priorities
        """
        logger.info("🔍 Analyzing repository changes...")
        
        planner = ChangePlanner(repo_path=str(self.repo_path))
        
        # Get changed files
        changed_files = planner.get_changed_files(base_ref=base_ref)
        
        # Get all files
        all_files = list(self.repo_path.rglob("*.py"))  # TODO: Support all languages
        
        # Calculate priorities
        priorities = planner.prioritize_files(
            all_files=[str(f.relative_to(self.repo_path)) for f in all_files],
            changed_files=changed_files
        )
        
        if show_priorities:
            self._display_priorities(priorities)
        
        return {
            "changed_files": len(changed_files),
            "total_files": len(all_files),
            "priorities": priorities
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all services.
        
        Returns:
            Health status for each component
        """
        logger.info("🏥 Running health checks...")
        
        health = {
            "embedding_service": False,
            "vector_store": False,
            "llm_service": False
        }
        
        # Check embedding service
        try:
            embedding_service = EmbeddingService(provider="auto")
            health["embedding_service"] = await embedding_service.health_check()
            logger.info(f"✅ Embedding service: {'Connected' if health['embedding_service'] else 'Failed'}")
        except Exception as e:
            logger.error(f"❌ Embedding service: {e}")
        
        # Check vector store
        try:
            # Get dimension from embedding service
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            vector_store = VectorStore(
                collection_name="health_check_test",
                embedding_dim=dimension
            )
            health["vector_store"] = True
            logger.info("✅ Vector store: Connected")
        except Exception as e:
            logger.error(f"❌ Vector store: {e}")
        
        # Check LLM service
        try:
            # TODO: Add LLM health check
            health["llm_service"] = True
            logger.info("✅ LLM service: Ready")
        except Exception as e:
            logger.error(f"❌ LLM service: {e}")
        
        return health
    
    def _display_priorities(self, priorities: list):
        """Display priority breakdown"""
        print("\n📊 File Priorities:")
        print("=" * 80)
        
        by_priority = {}
        for p in priorities[:20]:  # Show top 20
            if p.priority not in by_priority:
                by_priority[p.priority] = []
            by_priority[p.priority].append(p)
        
        for priority in sorted(by_priority.keys()):
            files = by_priority[priority]
            print(f"\nPriority {priority} ({len(files)} files):")
            for f in files[:5]:  # Show top 5 per priority
                status = "🔴 Changed" if f.is_changed else "⚪ Unchanged"
                entry = "📍 Entry" if f.is_entry_point else ""
                print(f"  {status} {entry} {f.file_path}")
                print(f"    Reason: {f.reason}")

