"""
Cleanup command handler.
"""

from orchestrator import CodeIntelligenceOrchestrator


async def cmd_cleanup(args):
    """Handle cleanup command"""
    orchestrator = CodeIntelligenceOrchestrator(repo_path=args.repo)
    
    # Determine what to clean
    collection = args.collection
    repository = args.repository
    
    if not collection and not repository:
        print("\n❌ Error: Must specify either --collection or --repository")
        print("   Use --help for usage information")
        return
    
    # Show what will be deleted
    target = collection if collection else f"{repository} (as collection)"
    print(f"\n⚠️  WARNING: This will permanently delete all embeddings!")
    print(f"   Target: {target}")
    
    if not args.force:
        print("\n   To proceed, add --force flag:")
        if collection:
            print(f"   python main.py cleanup --collection {collection} --force")
        else:
            print(f"   python main.py cleanup --repository {repository} --force")
        return
    
    # Perform cleanup
    result = await orchestrator.cleanup(
        collection_name=collection,
        github_repository=repository,
        confirm=args.force
    )
    
    if not result.get("success"):
        print(f"\n❌ Cleanup failed: {result.get('error')}")
        if result.get("warning"):
            print(f"   {result['warning']}")
        return
    
    # Display success
    print(f"\n✅ Cleanup Complete!")
    print("=" * 60)
    print(f"   Collection: {result['collection_name']}")
    print(f"   Vectors deleted: {result['vectors_deleted']}")
    print(f"\n   {result['message']}")
