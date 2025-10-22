"""
Embed command handler.
"""

from orchestrator import CodeIntelligenceOrchestrator


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
