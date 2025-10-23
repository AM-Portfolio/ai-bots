"""
Query command handler.
"""

import logging
from utils.enhanced_query import EnhancedQueryService

logger = logging.getLogger(__name__)


async def cmd_query(args):
    """Handle query command"""
    # Use enhanced query service
    query_service = EnhancedQueryService(collection_name=args.collection)
    
    results = await query_service.search(
        query_text=args.query,
        limit=args.limit,
        score_threshold=args.threshold
    )
    
    if not results.get("success"):
        print(f"\n❌ Error: {results.get('error')}")
        return
    
    # Display summary
    print(f"\n🔍 Query Results:")
    print("=" * 80)
    print(f"Query: {results['query']}")
    print(f"Collection: {results['collection']}")
    print(f"\n{results['summary']}\n")
    
    # Display results
    for result in results.get("results", []):
        print(f"\n{result['rank']}. {result['file_path']}")
        print(f"   Relevance: {result['relevance']} (score: {result['score']})")
        print(f"   Lines: {result['start_line']}-{result['end_line']} | Language: {result['language']}")
        print(f"   Code Preview:")
        
        # Show first few lines of code
        code_lines = result['code'].split('\n')[:5]
        for line in code_lines:
            print(f"      {line}")
        
        total_lines = len(result['code'].split('\n'))
        if total_lines > 5:
            remaining_lines = total_lines - 5
            print(f"      ... ({remaining_lines} more lines)")
        
        # Show metadata if available
        metadata = result.get('metadata', {})
        if metadata.get('functions'):
            print(f"   Functions: {', '.join(metadata['functions'][:3])}")
        if metadata.get('classes'):
            print(f"   Classes: {', '.join(metadata['classes'][:3])}")
    
    # Display search metadata
    search_meta = results.get('search_metadata', {})
    print(f"\n\n📊 Search Statistics:")
    print(f"   Total searched: {search_meta.get('total_searched', 0)}")
    print(f"   Threshold: {search_meta.get('threshold_applied', 0.0)}")
    print(f"   Best score: {search_meta.get('best_score', 0.0)}")
    print(f"   Average score: {search_meta.get('average_score', 0.0)}")
