"""
Analyze command handler (git-based change analysis).
"""

from orchestrator import CodeIntelligenceOrchestrator


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
