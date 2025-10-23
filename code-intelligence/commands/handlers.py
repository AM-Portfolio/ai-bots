"""
Command handlers for CLI interface
"""
import logging
from pathlib import Path
from typing import Any

from analysis.github_analyzer import GitHubAnalyzer
from analysis.change_analyzer import ChangeAnalyzer
from analysis.health_checker import HealthChecker

logger = logging.getLogger(__name__)


async def handle_embed(
    repo_path: str,
    collection_name: str,
    max_files: int = None,
    force_reindex: bool = False,
    github_repository: str = None,
    query: str = None,
    language: str = None
) -> dict:
    """Handle embed command"""
    from orchestrator import CodeIntelligenceOrchestrator
    
    orchestrator = CodeIntelligenceOrchestrator(repo_path=repo_path)
    stats = await orchestrator.embed_repository(
        collection_name=collection_name,
        max_files=max_files,
        force_reindex=force_reindex,
        github_repository=github_repository,
        query=query,
        language=language
    )
    
    return stats


async def handle_summarize(
    repo_path: str,
    files: list = None,
    force: bool = False
) -> dict:
    """Handle summarize command"""
    from orchestrator import CodeIntelligenceOrchestrator
    
    orchestrator = CodeIntelligenceOrchestrator(repo_path=repo_path)
    results = await orchestrator.generate_summaries(
        files=files,
        force=force
    )
    
    return results


async def handle_analyze(
    repo_path: str,
    base_ref: str = "HEAD",
    show_priorities: bool = True
) -> dict:
    """Handle analyze command (git-based change analysis)"""
    analyzer = ChangeAnalyzer(repo_path=Path(repo_path))
    results = analyzer.analyze_changes(base_ref=base_ref)
    
    if show_priorities:
        analyzer.display_priorities(results["priorities"])
    
    return results


async def handle_repo_analyze(
    repository: str,
    query: str = None,
    max_results: int = 10,
    language: str = None
) -> dict:
    """Handle repo-analyze command (GitHub LLM-based repository analysis)"""
    analyzer = GitHubAnalyzer()
    results = await analyzer.analyze_repository(
        repository=repository,
        query=query,
        max_results=max_results,
        language=language
    )
    
    # Format and display results
    print(analyzer.format_results(results, max_display=max_results))
    
    return results


async def handle_health(repo_path: str) -> dict:
    """Handle health command"""
    checker = HealthChecker()
    health = await checker.check_all()
    
    # Format and display results
    print(checker.format_results(health))
    
    return health


async def handle_test(repo_path: str):
    """Handle test command"""
    print("🧪 Running integration tests...")
    try:
        from tests.test_pipeline import main as test_main
        await test_main()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
