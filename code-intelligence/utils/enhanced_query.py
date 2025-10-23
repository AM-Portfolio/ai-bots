"""
Enhanced query functionality for code intelligence.

Provides rich search results with formatting, scoring, and metadata.
"""

import logging
from typing import Dict, Any, List
from shared.vector_db.embedding_service import EmbeddingService
from storage.vector_store import VectorStore

logger = logging.getLogger(__name__)


class EnhancedQueryService:
    """Enhanced query service with better result formatting"""
    
    def __init__(self, collection_name: str = "code_intelligence"):
        """
        Initialize query service.
        
        Args:
            collection_name: Qdrant collection name (repository identifier)
        """
        self.collection_name = collection_name
        self.embedding_service = EmbeddingService(provider="auto")
        dimension = self.embedding_service.get_dimension()
        self.vector_store = VectorStore(
            collection_name=collection_name,
            embedding_dim=dimension
        )
    
    async def search(
        self,
        query_text: str,
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for relevant code with enhanced results.
        
        Args:
            query_text: Natural language query or code search
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            Enhanced search results with:
            - Relevant code chunks with scores
            - File paths and locations
            - Formatted code with syntax
            - Metadata (language, imports, etc.)
        """
        logger.info(f"🔍 Querying '{self.collection_name}': {query_text}")
        
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query_text)
            
            # Search vector store
            raw_results = self.vector_store.search(
                query_vector=query_embedding,
                limit=limit * 2  # Get more results to filter by threshold
            )
            
            # Filter by score threshold and format results
            formatted_results = []
            for result in raw_results:
                score = result.get("score", 0.0)
                
                # Apply score threshold
                if score < score_threshold:
                    continue
                
                if len(formatted_results) >= limit:
                    break
                
                # Extract payload data
                payload = result.get("payload", {})
                
                # Format result
                formatted_result = {
                    "rank": len(formatted_results) + 1,
                    "score": round(score, 4),
                    "relevance": self._get_relevance_label(score),
                    "file_path": payload.get("file_path", "unknown"),
                    "chunk_index": payload.get("chunk_index", 0),
                    "start_line": payload.get("start_line", 0),
                    "end_line": payload.get("end_line", 0),
                    "language": payload.get("language", "unknown"),
                    "code": payload.get("text", ""),
                    "metadata": {
                        "repo_path": payload.get("repo_path", ""),
                        "file_type": payload.get("file_type", ""),
                        "imports": payload.get("imports", []),
                        "functions": payload.get("functions", []),
                        "classes": payload.get("classes", [])
                    }
                }
                
                formatted_results.append(formatted_result)
            
            # Generate summary
            summary = self._generate_search_summary(
                query=query_text,
                results=formatted_results,
                total_searched=len(raw_results)
            )
            
            logger.info(f"✅ Found {len(formatted_results)} relevant results")
            
            return {
                "success": True,
                "query": query_text,
                "collection": self.collection_name,
                "summary": summary,
                "results_count": len(formatted_results),
                "results": formatted_results,
                "search_metadata": {
                    "total_searched": len(raw_results),
                    "threshold_applied": score_threshold,
                    "best_score": formatted_results[0]["score"] if formatted_results else 0.0,
                    "average_score": round(
                        sum(r["score"] for r in formatted_results) / len(formatted_results), 4
                    ) if formatted_results else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {
                "success": False,
                "query": query_text,
                "collection": self.collection_name,
                "error": str(e),
                "results_count": 0,
                "results": []
            }
    
    def _get_relevance_label(self, score: float) -> str:
        """Convert similarity score to human-readable relevance label"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Very Good"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.6:
            return "Fair"
        else:
            return "Low"
    
    def _generate_search_summary(
        self,
        query: str,
        results: List[Dict[str, Any]],
        total_searched: int
    ) -> str:
        """Generate a human-readable summary of search results"""
        if not results:
            return f"No relevant code found for query: '{query}'"
        
        # Get file distribution
        files = set(r["file_path"] for r in results)
        languages = set(r["language"] for r in results)
        
        # Build summary
        summary_parts = [
            f"Found {len(results)} relevant code chunks",
            f"across {len(files)} file(s)",
            f"in {', '.join(sorted(languages))} language(s)."
        ]
        
        # Add best match info
        best = results[0]
        summary_parts.append(
            f"Best match: {best['file_path']} "
            f"(lines {best['start_line']}-{best['end_line']}, "
            f"score: {best['score']})"
        )
        
        return " ".join(summary_parts)
