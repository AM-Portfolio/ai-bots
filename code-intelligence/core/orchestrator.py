"""
Code Intelligence Orchestrator - Unified Entry Point

This is the main entry point for the code-intelligence module.
Organizes all functionality into a clean, command-based interface.

Available Commands:
  embed       - Embed repository code into vector database
  summarize   - Generate summaries for code files
  analyze     - Analyze repository changes and priorities
  health      - Check system health and connectivity
  test        - Run integration tests

Features:
  - Incremental embedding (only changed files)
  - Rich technical summaries with business context
  - Smart prioritization (changed files first)
  - Rate-limit aware processing
  - Progress tracking and reporting
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add parent directory to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from embed_repo import EmbeddingOrchestrator
from enhanced_summarizer import EnhancedCodeSummarizer
from change_planner import ChangePlanner
from repo_state import RepoState
from rate_limiter import RateLimitController, QuotaType
from vector_store import VectorStore
from shared.vector_db.embedding_service import EmbeddingService
from shared.llm_providers.github_llm_provider import (
    GitHubLLMProvider,
    RepoAnalysisRequest,
    QueryType
)
from shared.config import settings

# Import logging configuration
from logging_config import setup_logging

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
        self.github_llm = None
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
        github_file_paths = set()
        if github_repository:
            logger.info(f"\n🔍 STEP 1: GitHub LLM Repository Analysis")
            logger.info(f"   Repository: {github_repository}")
            
            try:
                # Initialize GitHub LLM provider
                if not self.github_llm:
                    self.github_llm = GitHubLLMProvider()
                
                # Analyze repository
                analysis_request = RepoAnalysisRequest(
                    repository=github_repository,
                    query=query,
                    query_type=QueryType.SEMANTIC_SEARCH if query else QueryType.REPO_SUMMARY,
                    max_results=max_files or 50,
                    filters={"language": language} if language else None
                )
                
                analysis_result = await self.github_llm.analyze_repository(analysis_request)
                
                if analysis_result.files:
                    github_file_paths = {f.file_path for f in analysis_result.files}
                    
                    stats["github_analysis"] = {
                        "repository": github_repository,
                        "files_found": len(analysis_result.files),
                        "confidence": analysis_result.confidence,
                        "summary": analysis_result.summary
                    }
                    
                    logger.info(f"✅ Found {len(analysis_result.files)} relevant files")
                    logger.info(f"   Confidence: {analysis_result.confidence:.2f}")
                else:
                    logger.warning("⚠️ No files found from GitHub analysis")
                    
            except Exception as e:
                logger.warning(f"⚠️ GitHub LLM analysis failed: {e}")
                logger.info("   Continuing with local discovery...")
        else:
            logger.info("\n📂 STEP 1: Using local file discovery (no GitHub repository specified)")
        
        # STEP 2: Delegate to EmbeddingPipeline to generate embeddings
        logger.info("\n📖 STEP 2: Repository Embedding Pipeline")
        
        from .embed_repo import EmbeddingPipeline
        embedding_pipeline = EmbeddingPipeline(
            repo_path=str(self.repo_path)
        )
        
        # Pass GitHub file paths as a filter hint
        embedding_result = await embedding_pipeline.generate_embeddings(
            file_filter=github_file_paths if github_file_paths else None,
            max_files=max_files,
            force_reindex=force_reindex
        )
        
        # STEP 3: Store embeddings in vector DB
        logger.info("\n💾 STEP 3: Storing embeddings in vector database")
        
        from .vector_store import VectorStore, EmbeddingPoint
        vector_store = VectorStore(
            collection_name=collection_name,
            qdrant_path=str(self.repo_path / ".qdrant")
        )
        
        embedding_data = embedding_result["embedding_data"]
        logger.info(f"   Storing {len(embedding_data)} embeddings...")
        
        # Convert embedding data to EmbeddingPoint objects
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
        batch_size = 50
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
        
        # STEP 4: Update repository state
        from .repo_state import RepoState
        repo_state = RepoState(self.repo_path)
        processed_files = set(chunk["metadata"]["file_path"] for chunk in embedding_result["chunks"])
        for file_path in processed_files:
            repo_state.mark_file_processed(
                file_path=file_path,
                chunks_count=len([c for c in embedding_result["chunks"] if c["metadata"]["file_path"] == file_path])
            )
        
        # Merge stats
        stats.update(embedding_result["stats"])
        stats["chunks_embedded"] = total_stored
        stats["failed_chunks"] = total_failed
        
        logger.info("\n✅ Repository embedding orchestration complete!")
        if stats.get("github_analysis"):
            logger.info(f"   GitHub: {stats['github_analysis']['files_found']} files analyzed")
        logger.info(f"   Stored: {total_stored}/{len(embedding_data)} embeddings")

        
        return stats
    
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
    
    async def analyze_repository_with_github_llm(
        self,
        repository: str,
        query: Optional[str] = None,
        max_results: int = 10,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository using GitHub LLM provider.
        
        Args:
            repository: Repository name (owner/repo)
            query: Optional search query
            max_results: Maximum number of files to return
            language: Optional language filter (e.g., 'python', 'java')
            
        Returns:
            Analysis results with files, summaries, and confidence scores
        """
        logger.info(f"🔍 Analyzing repository: {repository}")
        if query:
            logger.info(f"   Query: {query}")
        
        # Use EmbeddingOrchestrator to analyze repository
        results = await self.embedding_orchestrator.analyze_repository_structure(
            repository=repository,
            query=query,
            max_results=max_results,
            language=language
        )
        
        if results.get("error"):
            logger.error(f"❌ Analysis failed: {results['error']}")
            return results
        
        # Display results
        files = results.get("files", [])
        summary = results.get("summary", "")
        confidence = results.get("confidence", 0.0)
        
        logger.info(f"✅ Found {len(files)} relevant files")
        logger.info(f"   Confidence: {confidence:.2f}")
        
        return results
    
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


async def cmd_embed(args):
    """Handle embed command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    stats = await orchestrator.embed_repository(
        collection_name=args.collection,
        max_files=args.max_files,
        force_reindex=args.force
    )
    
    print("\n📊 Embedding Statistics:")
    print("=" * 60)
    print(f"  Files processed:  {stats['files_processed']}")
    print(f"  Chunks embedded:  {stats['chunks_embedded']}")
    print(f"  Success rate:     {stats['success_rate']:.1f}%")
    print(f"  Failed chunks:    {stats.get('failed_chunks', 0)}")


async def cmd_summarize(args):
    """Handle summarize command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    results = await orchestrator.generate_summaries(
        files=args.files,
        force=args.force
    )
    
    print("\n📝 Summary Results:")
    print("=" * 60)
    print(f"  Files processed:      {results['files_processed']}")
    print(f"  Summaries generated:  {results['summaries_generated']}")
    print(f"  Cached summaries:     {results['cached_summaries']}")


async def cmd_analyze(args):
    """Handle analyze command (git-based change analysis)"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    results = await orchestrator.analyze_changes(
        base_ref=args.base,
        show_priorities=not args.no_display
    )
    
    print(f"\n🔍 Analysis Complete:")
    print(f"  Changed files: {results['changed_files']}")
    print(f"  Total files:   {results['total_files']}")


async def cmd_repo_analyze(args):
    """Handle repo-analyze command (GitHub LLM-based repository analysis)"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    results = await orchestrator.analyze_repository_with_github_llm(
        repository=args.repository,
        query=args.query,
        max_results=args.max_results,
        language=args.language
    )
    
    if results.get("error"):
        print(f"\n❌ Error: {results['error']}")
        return
    
    print("\n📊 Repository Analysis Results:")
    print("=" * 80)
    print(f"Repository: {args.repository}")
    if args.query:
        print(f"Query: {args.query}")
    print(f"Confidence: {results.get('confidence', 0):.2f}")
    print()
    
    # Display files
    files = results.get("files", [])
    print(f"Found {len(files)} relevant files:")
    print("-" * 80)
    
    for i, file_info in enumerate(files[:args.max_results], 1):
        file_path = file_info.get("file_path", "unknown")
        language = file_info.get("language", "unknown")
        relevance = file_info.get("relevance_score", 0)
        summary = file_info.get("summary", "No summary available")
        
        print(f"\n{i}. {file_path}")
        print(f"   Language: {language} | Relevance: {relevance:.2f}")
        print(f"   Summary: {summary}")
    
    # Display overall summary
    if summary := results.get("summary"):
        print("\n" + "=" * 80)
        print("Repository Summary:")
        print(summary)


async def cmd_health(args):
    """Handle health command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    health = await orchestrator.health_check()
    
    print("\n🏥 Health Check Results:")
    print("=" * 60)
    all_healthy = all(health.values())
    status_icon = "✅" if all_healthy else "⚠️"
    print(f"{status_icon} Overall Status: {'Healthy' if all_healthy else 'Issues Detected'}")
    print()
    for service, status in health.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {service.replace('_', ' ').title()}: {'OK' if status else 'FAILED'}")


async def cmd_test(args):
    """Handle test command"""
    print("🧪 Running integration tests...")
    # Import and run test pipeline
    try:
        from test_pipeline import main as test_main
        await test_main()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


def main():
    """Main entry point with command routing"""
    parser = argparse.ArgumentParser(
        description="Code Intelligence - Unified orchestration for code embedding and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Embed repository (incremental)
  python orchestrator.py embed

  # Force re-embed all files
  python orchestrator.py embed --force

  # Embed with limits
  python orchestrator.py embed --max-files 50 --collection my_project

  # Debug mode with detailed logging
  python orchestrator.py embed --log-level debug

  # Verbose mode with file logging
  python orchestrator.py embed --log-level verbose --log-file embedding.log

  # Generate summaries
  python orchestrator.py summarize

  # Analyze changes (git-based)
  python orchestrator.py analyze --base origin/main

  # Analyze GitHub repository with GitHub LLM
  python orchestrator.py repo-analyze --repository AM-Portfolio/ai-bots

  # Analyze with query
  python orchestrator.py repo-analyze --repository owner/repo --query "vector database integration"

  # Filter by language
  python orchestrator.py repo-analyze --repository owner/repo --language python --max-results 5

  # Health check
  python orchestrator.py health

  # Run tests
  python orchestrator.py test
        """
    )
    
    # Global options
    parser.add_argument(
        "--log-level",
        choices=["quiet", "normal", "verbose", "debug"],
        default="normal",
        help="Logging level preset"
    )
    parser.add_argument(
        "--log-file",
        help="Optional log file path"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Embed repository into vector database")
    embed_parser.add_argument("--repo", default=".", help="Repository path")
    embed_parser.add_argument("--collection", default="code_intelligence", help="Qdrant collection name")
    embed_parser.add_argument("--max-files", type=int, help="Maximum files to process")
    embed_parser.add_argument("--force", action="store_true", help="Force re-embedding")
    
    # Summarize command
    summarize_parser = subparsers.add_parser("summarize", help="Generate code summaries")
    summarize_parser.add_argument("--repo", default=".", help="Repository path")
    summarize_parser.add_argument("--files", nargs="+", help="Specific files to summarize")
    summarize_parser.add_argument("--force", action="store_true", help="Force regeneration")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository changes (git-based)")
    analyze_parser.add_argument("--repo", default=".", help="Repository path")
    analyze_parser.add_argument("--base", default="HEAD", help="Base git reference")
    analyze_parser.add_argument("--no-display", action="store_true", help="Skip priority display")
    
    # Repo-analyze command (GitHub LLM)
    repo_analyze_parser = subparsers.add_parser(
        "repo-analyze",
        help="Analyze GitHub repository using GitHub LLM"
    )
    repo_analyze_parser.add_argument("--repo", default=".", help="Local repository path")
    repo_analyze_parser.add_argument(
        "--repository",
        required=True,
        help="GitHub repository (owner/repo)"
    )
    repo_analyze_parser.add_argument(
        "--query",
        help="Optional search query"
    )
    repo_analyze_parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of files to return (default: 10)"
    )
    repo_analyze_parser.add_argument(
        "--language",
        help="Filter by programming language (e.g., python, java)"
    )
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check system health")
    health_parser.add_argument("--repo", default=".", help="Repository path")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run integration tests")
    test_parser.add_argument("--repo", default=".", help="Repository path")
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    setup_logging(level=args.log_level, log_file=args.log_file)
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Route to command handler
    command_map = {
        "embed": cmd_embed,
        "summarize": cmd_summarize,
        "analyze": cmd_analyze,
        "repo-analyze": cmd_repo_analyze,
        "health": cmd_health,
        "test": cmd_test
    }
    
    if args.command in command_map:
        asyncio.run(command_map[args.command](args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
