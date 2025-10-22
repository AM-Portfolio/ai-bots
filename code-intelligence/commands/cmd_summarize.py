"""
Summarize command handler.
"""

from orchestrator import CodeIntelligenceOrchestrator


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
