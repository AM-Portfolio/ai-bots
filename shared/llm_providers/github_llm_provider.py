"""
GitHub LLM Provider

Provides repository analysis and code intelligence using vector search
and GitHub API integration. Can analyze repository structure, files,
and provide semantic code search.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from shared.vector_db.services.vector_query_service import VectorQueryService
from shared.clients.wrappers.github_wrapper import GitHubWrapper

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries supported"""
    CODE_SEARCH = "code_search"
    REPO_SUMMARY = "repo_summary"
    FILE_EXPLANATION = "file_explanation"
    SEMANTIC_SEARCH = "semantic_search"
    DOCUMENTATION = "documentation"
    REPO_STRUCTURE = "repo_structure"


@dataclass
class RepoAnalysisRequest:
    """Request for repository analysis"""
    repository: str  # owner/repo format
    query: Optional[str] = None
    query_type: QueryType = QueryType.REPO_STRUCTURE
    max_results: int = 10
    include_vector_search: bool = True
    include_github_api: bool = True
    file_pattern: Optional[str] = None  # glob pattern like "*.py"
    language: Optional[str] = None


@dataclass
class FileResult:
    """Individual file result"""
    file_path: str
    content: Optional[str] = None
    summary: Optional[str] = None
    language: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RepoAnalysisResponse:
    """Response from repository analysis"""
    repository: str
    query: Optional[str]
    query_type: QueryType
    files: List[FileResult]
    summary: str
    confidence_score: float
    metadata: Dict[str, Any]


class GitHubLLMProvider:
    """
    GitHub LLM Provider for repository analysis and code intelligence.
    
    Features:
    - Repository structure analysis
    - Semantic code search via vector DB
    - File content retrieval from GitHub
    - Code intelligence with enhanced summaries
    """
    
    def __init__(
        self,
        vector_service: Optional[VectorQueryService] = None,
        github_client: Optional[GitHubWrapper] = None
    ):
        """
        Initialize GitHub LLM Provider
        
        Args:
            vector_service: Vector database query service
            github_client: GitHub API client wrapper
        """
        self.vector_service = vector_service
        self.github_client = github_client
        logger.info("🐙 GitHub LLM Provider initialized")
    
    async def analyze_repository(
        self,
        request: RepoAnalysisRequest
    ) -> RepoAnalysisResponse:
        """
        Analyze repository and return file details
        
        Args:
            request: Repository analysis request
            
        Returns:
            RepoAnalysisResponse with file details and summaries
        """
        logger.info(f"📂 Analyzing repository: {request.repository}")
        logger.info(f"   Query type: {request.query_type.value}")
        logger.info(f"   Query: {request.query or 'None'}")
        
        files = []
        
        # Strategy 1: Vector search (if query provided and vector service available)
        if request.query and request.include_vector_search and self.vector_service:
            logger.info("🔍 Performing vector search...")
            vector_files = await self._search_vector_db(request)
            files.extend(vector_files)
            logger.info(f"   Found {len(vector_files)} files from vector search")
        
        # Strategy 2: GitHub API direct (list files in repo)
        if request.include_github_api and self.github_client:
            logger.info("📡 Fetching from GitHub API...")
            github_files = await self._fetch_github_files(request)
            files.extend(github_files)
            logger.info(f"   Found {len(github_files)} files from GitHub API")
        
        # Deduplicate and rank
        unique_files = self._deduplicate_files(files)
        ranked_files = self._rank_files(unique_files, request)
        
        # Limit results
        final_files = ranked_files[:request.max_results]
        
        # Generate summary
        summary = self._generate_summary(final_files, request)
        
        # Calculate confidence
        confidence = self._calculate_confidence(final_files)
        
        logger.info(f"✅ Analysis complete: {len(final_files)} files returned")
        
        return RepoAnalysisResponse(
            repository=request.repository,
            query=request.query,
            query_type=request.query_type,
            files=final_files,
            summary=summary,
            confidence_score=confidence,
            metadata={
                'total_files_found': len(unique_files),
                'vector_search_used': request.include_vector_search and bool(request.query),
                'github_api_used': request.include_github_api
            }
        )
    
    async def _search_vector_db(
        self,
        request: RepoAnalysisRequest
    ) -> List[FileResult]:
        """
        Search vector database for relevant files
        
        Args:
            request: Analysis request with query
            
        Returns:
            List of file results from vector search
        """
        try:
            # Build filters
            filters = {'repo_name': request.repository}
            if request.language:
                filters['language'] = request.language
            
            # Perform semantic search
            vector_results = await self.vector_service.semantic_search(
                query=request.query,
                top_k=request.max_results * 2,  # Get more to filter
                filters=filters
            )
            
            # Convert to FileResult
            file_results = []
            for vr in vector_results:
                file_result = FileResult(
                    file_path=vr.metadata.file_path or "unknown",
                    content=vr.content,
                    summary=vr.metadata.get('summary'),
                    language=vr.metadata.language,
                    relevance_score=vr.score,
                    metadata={
                        'doc_id': vr.doc_id,
                        'repo': vr.metadata.repo_name,
                        'source': 'vector_db',
                        'chunk_type': vr.metadata.content_type
                    }
                )
                file_results.append(file_result)
            
            return file_results
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    async def _fetch_github_files(
        self,
        request: RepoAnalysisRequest
    ) -> List[FileResult]:
        """
        Fetch file list from GitHub API
        
        Args:
            request: Analysis request
            
        Returns:
            List of file results from GitHub
        """
        try:
            owner, repo = request.repository.split('/')
            
            # Get repository tree
            tree = await self.github_client.get_repo_tree(
                owner=owner,
                repo=repo,
                recursive=True
            )
            
            file_results = []
            for item in tree:
                # Skip directories
                if item.get('type') != 'blob':
                    continue
                
                file_path = item.get('path', '')
                
                # Apply file pattern filter
                if request.file_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(file_path, request.file_pattern):
                        continue
                
                # Apply language filter (basic extension check)
                if request.language:
                    lang_ext_map = {
                        'python': ['.py'],
                        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
                        'java': ['.java'],
                        'kotlin': ['.kt', '.kts'],
                        'dart': ['.dart']
                    }
                    extensions = lang_ext_map.get(request.language.lower(), [])
                    if not any(file_path.endswith(ext) for ext in extensions):
                        continue
                
                file_result = FileResult(
                    file_path=file_path,
                    content=None,  # Don't fetch content yet (too expensive)
                    language=self._detect_language(file_path),
                    relevance_score=0.5,  # Default score for GitHub API results
                    metadata={
                        'sha': item.get('sha'),
                        'size': item.get('size'),
                        'url': item.get('url'),
                        'source': 'github_api'
                    }
                )
                file_results.append(file_result)
            
            return file_results
            
        except Exception as e:
            logger.error(f"❌ GitHub API fetch failed: {e}")
            return []
    
    def _deduplicate_files(self, files: List[FileResult]) -> List[FileResult]:
        """Remove duplicate files, keeping highest relevance score"""
        unique_files = {}
        
        for file in files:
            key = file.file_path
            if key not in unique_files or file.relevance_score > unique_files[key].relevance_score:
                unique_files[key] = file
        
        return list(unique_files.values())
    
    def _rank_files(
        self,
        files: List[FileResult],
        request: RepoAnalysisRequest
    ) -> List[FileResult]:
        """Rank files by relevance"""
        # Sort by relevance score
        return sorted(files, key=lambda f: f.relevance_score, reverse=True)
    
    def _generate_summary(
        self,
        files: List[FileResult],
        request: RepoAnalysisRequest
    ) -> str:
        """Generate summary of analysis results"""
        if not files:
            return f"No files found in repository {request.repository}"
        
        summary_parts = [
            f"Repository: {request.repository}",
            f"Files found: {len(files)}",
            ""
        ]
        
        # Group by language
        by_language = {}
        for file in files:
            lang = file.language or 'unknown'
            by_language[lang] = by_language.get(lang, 0) + 1
        
        summary_parts.append("Language distribution:")
        for lang, count in sorted(by_language.items(), key=lambda x: x[1], reverse=True):
            summary_parts.append(f"  - {lang}: {count} files")
        
        summary_parts.append("")
        summary_parts.append("Top files:")
        for idx, file in enumerate(files[:5], 1):
            score_str = f" (relevance: {file.relevance_score:.2f})" if file.relevance_score > 0 else ""
            summary_parts.append(f"  {idx}. {file.file_path}{score_str}")
        
        return "\n".join(summary_parts)
    
    def _calculate_confidence(self, files: List[FileResult]) -> float:
        """Calculate confidence score based on results"""
        if not files:
            return 0.0
        
        # Average of top 3 relevance scores
        top_scores = [f.relevance_score for f in files[:3] if f.relevance_score > 0]
        if not top_scores:
            return 0.5  # Default if no scores available
        
        return sum(top_scores) / len(top_scores)
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.dart': 'dart',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext_map.get(ext)


# Convenience function for quick repository analysis
async def analyze_repository(
    repository: str,
    query: Optional[str] = None,
    max_results: int = 10,
    vector_service: Optional[VectorQueryService] = None,
    github_client: Optional[GitHubWrapper] = None
) -> RepoAnalysisResponse:
    """
    Quick helper to analyze a repository
    
    Args:
        repository: Repository in owner/repo format
        query: Optional query for semantic search
        max_results: Maximum number of files to return
        vector_service: Vector database service
        github_client: GitHub API client
        
    Returns:
        RepoAnalysisResponse with file details
    """
    provider = GitHubLLMProvider(
        vector_service=vector_service,
        github_client=github_client
    )
    
    request = RepoAnalysisRequest(
        repository=repository,
        query=query,
        max_results=max_results,
        query_type=QueryType.REPO_STRUCTURE if not query else QueryType.SEMANTIC_SEARCH
    )
    
    return await provider.analyze_repository(request)
