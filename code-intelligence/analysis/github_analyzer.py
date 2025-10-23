"""
GitHub analysis module - handles GitHub repository analysis using LLM
"""
import logging
from typing import Optional, Dict, Any, Set

from shared.llm_providers.github_llm_provider import (
    GitHubLLMProvider,
    RepoAnalysisRequest,
    QueryType
)
from shared.clients.wrappers.github_wrapper import GitHubWrapper
from shared.vector_db.services.vector_query_service import VectorQueryService

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """Handles GitHub repository analysis using LLM"""
    
    def __init__(self, vector_service: Optional[VectorQueryService] = None, github_client: Optional[GitHubWrapper] = None):
        self.vector_service = vector_service
        self.github_client = github_client
        self.github_llm = None
    
    async def analyze_repository(
        self,
        repository: str,
        query: Optional[str] = None,
        max_results: int = 50,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository to find relevant files.
        
        Args:
            repository: Repository name (owner/repo)
            query: Optional search query
            max_results: Maximum number of files
            language: Optional language filter
            
        Returns:
            Analysis results with file paths and metadata
        """
        logger.info(f"\n🔍 GitHub LLM Repository Analysis")
        logger.info(f"   Repository: {repository}")
        
        try:
            # Initialize GitHub LLM provider with clients
            if not self.github_llm:
                # Initialize GitHub client if not provided
                if not self.github_client:
                    self.github_client = GitHubWrapper()
                
                self.github_llm = GitHubLLMProvider(
                    vector_service=self.vector_service,
                    github_client=self.github_client
                )
            
            # Analyze repository
            analysis_request = RepoAnalysisRequest(
                repository=repository,
                query=query,
                query_type=QueryType.SEMANTIC_SEARCH if query else QueryType.REPO_SUMMARY,
                max_results=max_results,
                language=language
            )
            
            result = await self.github_llm.analyze_repository(analysis_request)
            
            if result.files:
                file_paths = {f.file_path for f in result.files}
                
                logger.info(f"✅ Found {len(result.files)} relevant files")
                logger.info(f"   Confidence: {result.confidence:.2f}")
                
                return {
                    "success": True,
                    "file_paths": file_paths,
                    "files_found": len(result.files),
                    "confidence": result.confidence,
                    "summary": result.summary,
                    "files": result.files
                }
            else:
                logger.warning("⚠️ No files found from GitHub analysis")
                return {
                    "success": False,
                    "file_paths": set(),
                    "files_found": 0,
                    "error": "No files found"
                }
                
        except Exception as e:
            logger.warning(f"⚠️ GitHub LLM analysis failed: {e}")
            return {
                "success": False,
                "file_paths": set(),
                "files_found": 0,
                "error": str(e)
            }
    
    def format_results(self, results: Dict[str, Any], max_display: int = 10) -> str:
        """Format analysis results for display"""
        if not results.get("success"):
            return f"❌ Analysis failed: {results.get('error', 'Unknown error')}"
        
        output = []
        output.append(f"📊 Repository Analysis Results")
        output.append("=" * 80)
        output.append(f"Files found: {results['files_found']}")
        output.append(f"Confidence: {results['confidence']:.2f}")
        output.append("")
        
        files = results.get("files", [])
        for i, file_info in enumerate(files[:max_display], 1):
            file_path = file_info.file_path if hasattr(file_info, 'file_path') else "unknown"
            language = file_info.language if hasattr(file_info, 'language') else "unknown"
            relevance = file_info.relevance_score if hasattr(file_info, 'relevance_score') else 0
            
            output.append(f"\n{i}. {file_path}")
            output.append(f"   Language: {language} | Relevance: {relevance:.2f}")
        
        if results.get("summary"):
            output.append("\n" + "=" * 80)
            output.append("Summary:")
            output.append(results["summary"])
        
        return "\n".join(output)
