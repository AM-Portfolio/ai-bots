"""
Vector Database Module

Provides vector storage and semantic search capabilities for repository content.
Supports multiple vector database providers with a unified interface.
"""

from .base import VectorDBProvider, VectorSearchResult, DocumentMetadata
from .factory import VectorDBFactory
from .embedding_service import EmbeddingService

__all__ = [
    'VectorDBProvider',
    'VectorSearchResult', 
    'DocumentMetadata',
    'VectorDBFactory',
    'EmbeddingService'
]
