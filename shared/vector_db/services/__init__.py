"""
Vector DB Services

Note: Repository indexing has been moved to code-intelligence module
for advanced features like tree-sitter parsing, enhanced summarization,
and smart prioritization.
"""

from .vector_query_service import VectorQueryService

__all__ = ['VectorQueryService']
