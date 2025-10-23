"""
Repository analyze command handler (GitHub LLM-based analysis).
"""

import logging
from analysis.github_analyzer import GitHubAnalyzer

logger = logging.getLogger(__name__)


async def cmd_repo_analyze(args):
    """Handle repo-analyze command (GitHub LLM-based repository analysis)"""
    # Use GitHubAnalyzer directly
    github_analyzer = GitHubAnalyzer()
    
    logger.info(f"🔍 Analyzing repository: {args.repository}")
    if args.query:
        logger.info(f"   Query: {args.query}")
    
    analysis_result = await github_analyzer.analyze_repository(
        repository=args.repository,
        query=args.query,
        max_results=args.max_results,
        language=args.language
    )
    
    # Convert to results format
    if analysis_result.get("error"):
        results = {"error": analysis_result["error"]}
    else:
        logger.info(f"✅ Found {analysis_result['files_found']} relevant files")
        logger.info(f"   Confidence: {analysis_result['confidence']:.2f}")
        
        results = {
            "files": [{"file_path": fp, "language": "", "relevance_score": 0, "summary": ""} for fp in analysis_result["file_paths"]],
            "summary": analysis_result["summary"],
            "confidence": analysis_result["confidence"]
        }
    
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
