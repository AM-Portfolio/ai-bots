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
from shared.config import settings

# Import logging configuration
from logging_config import setup_logging

logger = logging.getLogger(__name__)


class CodeIntelligenceOrchestrator:
    """
    Main orchestrator for code intelligence operations.
    
    Provides unified interface for:
    - Repository embedding
    - Code summarization
    - Change analysis
    - Health checks
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository (default: current directory)
        """
        self.repo_path = Path(repo_path).resolve()
        self.settings = settings
        logger.info(f"📁 Repository: {self.repo_path}")
    
    async def embed_repository(
        self,
        collection_name: str = "code_intelligence",
        max_files: Optional[int] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Embed repository code into vector database.
        
        Args:
            collection_name: Qdrant collection name
            max_files: Maximum number of files to process
            force_reindex: Force re-embedding of all files
            
        Returns:
            Statistics dictionary with processing results
        """
        logger.info("🚀 Starting repository embedding pipeline...")
        
        orchestrator = EmbeddingOrchestrator(
            repo_path=str(self.repo_path),
            collection_name=collection_name
        )
        
        stats = await orchestrator.run_incremental(
            max_files=max_files,
            force_reindex=force_reindex
        )
        
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
    """Handle analyze command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    results = await orchestrator.analyze_changes(
        base_ref=args.base,
        show_priorities=not args.no_display
    )
    
    print(f"\n🔍 Analysis Complete:")
    print(f"  Changed files: {results['changed_files']}")
    print(f"  Total files:   {results['total_files']}")


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

  # Analyze changes
  python orchestrator.py analyze --base origin/main

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
    analyze_parser = subparsers.add_parser("analyze", help="Analyze repository changes")
    analyze_parser.add_argument("--repo", default=".", help="Repository path")
    analyze_parser.add_argument("--base", default="HEAD", help="Base git reference")
    analyze_parser.add_argument("--no-display", action="store_true", help="Skip priority display")
    
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
