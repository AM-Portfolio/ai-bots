#!/usr/bin/env python3
"""
Code Intelligence CLI - Main Entry Point

Command-line interface for code intelligence operations.
Handles argument parsing and routes to appropriate command handlers.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging
from commands import (
    cmd_embed,
    cmd_query,
    cmd_cleanup,
    cmd_summarize,
    cmd_analyze,
    cmd_repo_analyze,
    cmd_health,
    cmd_test
)


def main():
    """Main entry point with command routing"""
    parser = argparse.ArgumentParser(
        description="Code Intelligence - Unified orchestration for code embedding and analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Embed repository (incremental)
  python main.py embed

  # Force re-embed all files
  python main.py embed --force

  # Embed with limits
  python main.py embed --max-files 50 --collection my_project

  # Query for code
  python main.py query "vector database integration" --collection my_project

  # Cleanup/delete indexed data
  python main.py cleanup --collection my_project --force
  python main.py cleanup --repository owner/repo --force

  # Debug mode with detailed logging
  python main.py embed --log-level debug

  # Verbose mode with file logging
  python main.py embed --log-level verbose --log-file embedding.log

  # Generate summaries
  python main.py summarize

  # Analyze changes (git-based)
  python main.py analyze --base origin/main

  # Analyze GitHub repository with GitHub LLM
  python main.py repo-analyze --repository AM-Portfolio/ai-bots

  # Analyze with query
  python main.py repo-analyze --repository owner/repo --query "vector database integration"

  # Filter by language
  python main.py repo-analyze --repository owner/repo --language python --max-results 5

  # Health check
  python main.py health

  # Run tests
  python main.py test
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
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Search vector database for relevant code")
    query_parser.add_argument("query", help="Search query (natural language or code)")
    query_parser.add_argument("--collection", default="code_intelligence", help="Qdrant collection name")
    query_parser.add_argument("--limit", type=int, default=5, help="Maximum results (default: 5)")
    query_parser.add_argument("--threshold", type=float, default=0.7, help="Minimum score (default: 0.7)")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Delete indexed data from vector database")
    cleanup_parser.add_argument("--repo", default=".", help="Repository path")
    cleanup_parser.add_argument("--collection", help="Collection name to delete")
    cleanup_parser.add_argument("--repository", help="GitHub repository (owner/repo) to delete")
    cleanup_parser.add_argument("--force", action="store_true", help="Confirm deletion (required)")
    
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
        "query": cmd_query,
        "cleanup": cmd_cleanup,
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
