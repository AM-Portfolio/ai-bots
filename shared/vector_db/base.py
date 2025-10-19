"""
Base classes for Vector Database providers
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class DocumentMetadata:
    """Metadata for a document stored in vector DB"""
    doc_id: str
    source: str  # 'github', 'confluence', 'jira', etc.
    repo_name: Optional[str] = None
    file_path: Optional[str] = None
    commit_sha: Optional[str] = None
    content_type: str = 'text'  # 'code', 'markdown', 'text', 'docstring'
    language: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""
    doc_id: str
    content: str
    metadata: DocumentMetadata
    score: float  # Similarity score (0-1)
    embedding: Optional[List[float]] = None


class VectorDBProvider(ABC):
    """Abstract base class for vector database providers"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the vector database connection"""
        pass
    
    @abstractmethod
    async def create_collection(self, name: str, dimension: int) -> bool:
        """Create a new collection/index"""
        pass
    
    @abstractmethod
    async def add_documents(
        self,
        collection: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[DocumentMetadata]
    ) -> bool:
        """Add documents with embeddings to the collection"""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def delete_documents(
        self,
        collection: str,
        doc_ids: List[str]
    ) -> bool:
        """Delete documents by ID"""
        pass
    
    @abstractmethod
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get statistics about a collection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the vector DB is healthy"""
        pass
