"""
Qdrant Vector Database Provider
Production-ready vector database with persistence
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from ..base import VectorDBProvider, VectorSearchResult, DocumentMetadata

logger = logging.getLogger(__name__)


class QdrantProvider(VectorDBProvider):
    """Qdrant vector database provider with persistence"""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.client: Optional[QdrantClient] = None
        self.initialized = False
        logger.info(f"🗄️  Qdrant Provider initialized (host={host}, port={port})")
    
    async def initialize(self) -> bool:
        """Initialize connection to Qdrant"""
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            # Test connection
            collections = self.client.get_collections()
            self.initialized = True
            logger.info(f"✅ Connected to Qdrant at {self.host}:{self.port}")
            logger.info(f"📊 Existing collections: {len(collections.collections)}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            self.initialized = False
            return False
    
    async def create_collection(self, name: str, dimension: int) -> bool:
        """Create a new collection in Qdrant"""
        try:
            if not self.client:
                logger.error("❌ Qdrant client not initialized")
                return False
            
            # Check if collection already exists
            collections = self.client.get_collections()
            if any(c.name == name for c in collections.collections):
                logger.info(f"📦 Collection '{name}' already exists")
                return True
            
            # Create collection with cosine similarity
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"📦 Created collection '{name}' with dimension {dimension}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create collection '{name}': {e}")
            return False
    
    def _metadata_to_payload(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Convert DocumentMetadata to Qdrant payload"""
        payload = {
            'doc_id': metadata.doc_id,
            'source': metadata.source,
            'content_type': metadata.content_type,
        }
        
        # Add optional fields
        if metadata.repo_name:
            payload['repo_name'] = metadata.repo_name
        if metadata.file_path:
            payload['file_path'] = metadata.file_path
        if metadata.commit_sha:
            payload['commit_sha'] = metadata.commit_sha
        if metadata.language:
            payload['language'] = metadata.language
        if metadata.author:
            payload['author'] = metadata.author
        if metadata.created_at:
            payload['created_at'] = metadata.created_at.isoformat()
        if metadata.updated_at:
            payload['updated_at'] = metadata.updated_at.isoformat()
        if metadata.tags:
            payload['tags'] = ','.join(metadata.tags)  # Store as comma-separated string
        
        return payload
    
    def _payload_to_metadata(self, payload: Dict[str, Any]) -> DocumentMetadata:
        """Convert Qdrant payload to DocumentMetadata"""
        return DocumentMetadata(
            doc_id=payload.get('doc_id', ''),
            source=payload.get('source', ''),
            repo_name=payload.get('repo_name'),
            file_path=payload.get('file_path'),
            commit_sha=payload.get('commit_sha'),
            content_type=payload.get('content_type', 'text'),
            language=payload.get('language'),
            author=payload.get('author'),
            created_at=datetime.fromisoformat(payload['created_at']) if payload.get('created_at') else None,
            updated_at=datetime.fromisoformat(payload['updated_at']) if payload.get('updated_at') else None,
            tags=payload.get('tags', '').split(',') if payload.get('tags') else []
        )
    
    async def add_documents(
        self,
        collection: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[DocumentMetadata]
    ) -> bool:
        """Add documents to Qdrant collection"""
        try:
            if not self.client:
                logger.error("❌ Qdrant client not initialized")
                return False
            
            points = []
            for doc, embedding, metadata in zip(documents, embeddings, metadatas):
                payload = self._metadata_to_payload(metadata)
                payload['content'] = doc  # Store document content in payload
                
                point = PointStruct(
                    id=str(uuid.uuid4()),  # Generate unique point ID
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upload points in batches
            self.client.upsert(
                collection_name=collection,
                points=points
            )
            
            logger.info(f"✅ Added {len(documents)} documents to '{collection}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add documents to '{collection}': {e}")
            return False
    
    async def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar documents in Qdrant"""
        try:
            if not self.client:
                logger.warning("⚠️  Qdrant client not initialized")
                return []
            
            # Build filter if provided
            query_filter = None
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
                with_vectors=True
            )
            
            # Convert to VectorSearchResult
            results = []
            for hit in search_results:
                payload = hit.payload or {}
                metadata = self._payload_to_metadata(payload)
                
                # Convert vector to list if it exists
                embedding_list: Optional[List[float]] = None
                if hit.vector is not None:
                    try:
                        # Handle both list and other iterable types
                        if isinstance(hit.vector, list):
                            embedding_list = [float(x) if not isinstance(x, list) else float(x[0]) for x in hit.vector]
                        else:
                            embedding_list = list(hit.vector)  # type: ignore
                    except (ValueError, TypeError):
                        embedding_list = None
                
                result = VectorSearchResult(
                    doc_id=payload.get('doc_id', ''),
                    content=payload.get('content', ''),
                    metadata=metadata,
                    score=float(hit.score),
                    embedding=embedding_list
                )
                results.append(result)
            
            logger.info(f"🔍 Found {len(results)} results for query in '{collection}'")
            return results
        except Exception as e:
            logger.error(f"❌ Search failed in '{collection}': {e}")
            return []
    
    async def delete_documents(
        self,
        collection: str,
        doc_ids: List[str]
    ) -> bool:
        """Delete documents by ID from Qdrant"""
        try:
            if not self.client:
                logger.error("❌ Qdrant client not initialized")
                return False
            
            # Delete by filter (match doc_id)
            for doc_id in doc_ids:
                self.client.delete(
                    collection_name=collection,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="doc_id",
                                match=MatchValue(value=doc_id)
                            )
                        ]
                    )
                )
            
            logger.info(f"🗑️  Deleted {len(doc_ids)} documents from '{collection}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete documents from '{collection}': {e}")
            return False
    
    async def clear_collection(self, collection: str) -> bool:
        """Clear all documents from a collection"""
        try:
            if not self.client:
                logger.error("❌ Qdrant client not initialized")
                return False
            
            # Get collection stats first to see how many documents will be deleted
            stats = await self.get_collection_stats(collection)
            doc_count = stats.get('count', 0)
            
            if doc_count == 0:
                logger.info(f"📭 Collection '{collection}' is already empty")
                return True
            
            logger.info(f"🧹 Clearing {doc_count} documents from collection '{collection}'...")
            
            # Delete all points by not providing any filter (deletes all)
            self.client.delete(
                collection_name=collection,
                points_selector=Filter(must=[])  # Empty filter matches all
            )
            
            logger.info(f"✅ Successfully cleared all {doc_count} documents from '{collection}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear collection '{collection}': {e}")
            return False
    
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics from Qdrant"""
        try:
            if not self.client:
                return {}
            
            info = self.client.get_collection(collection_name=collection)
            
            # Get vector dimension - handle both dict and VectorParams types
            dimension = 768  # default
            if hasattr(info.config.params, 'vectors'):
                vectors_config = info.config.params.vectors
                if isinstance(vectors_config, dict):
                    # Multi-vector config
                    first_vector = next(iter(vectors_config.values()))
                    dimension = first_vector.size if first_vector else 768
                elif vectors_config:
                    # Single vector config
                    dimension = vectors_config.size
            
            return {
                'name': collection,
                'count': info.points_count,
                'dimension': dimension,
                'provider': 'qdrant',
                'status': info.status.value
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats for '{collection}': {e}")
            return {}
    
    async def list_collections(self) -> List[str]:
        """List all collection names in Qdrant"""
        try:
            if not self.client:
                logger.error("❌ Qdrant client not initialized")
                return []
            
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info(f"📋 Found {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check Qdrant health"""
        try:
            if not self.client:
                return False
            # Simple health check - try to get collections
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
