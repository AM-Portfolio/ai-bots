"""
Data models for GitHub-LLM module
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class QueryType(Enum):
    """Types of queries supported"""
    CODE_SEARCH = "code_search"
    REPO_SUMMARY = "repo_summary"
    FILE_EXPLANATION = "file_explanation"
    SEMANTIC_SEARCH = "semantic_search"
    DOCUMENTATION = "documentation"


@dataclass
class QueryRequest:
    """Request for GitHub-LLM query"""
    query: str
    query_type: QueryType = QueryType.SEMANTIC_SEARCH
    repository: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    max_results: int = 5
    include_vector_search: bool = True
    include_github_direct: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceResult:
    """Individual source result"""
    source_type: str  # 'vector_db', 'github_api'
    content: str
    metadata: Dict[str, Any]
    relevance_score: float


@dataclass
class QueryResponse:
    """Response from GitHub-LLM query"""
    query: str
    query_type: QueryType
    sources: List[SourceResult]
    summary: str
    beautified_response: str
    confidence_score: float
    processing_time_ms: float
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
