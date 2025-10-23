"""
In-Memory Vector Database Provider
Simple implementation for development and testing
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..base import VectorDBProvider, VectorSearchResult, DocumentMetadata

logger = logging.getLogger(__name__)


class InMemoryProvider(VectorDBProvider):
    """Simple in-memory vector database for development"""
    
    def __init__(self):
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        logger.info("🧠 In-Memory Vector DB Provider initialized")
    
    async def initialize(self) -> bool:
        """Initialize the in-memory database"""
        self.initialized = True
        logger.info("✅ In-Memory Vector DB initialized")
        return True
    
    async def create_collection(self, name: str, dimension: int) -> bool:
        """Create a new collection"""
        if name not in self.collections:
            self.collections[name] = {
                'dimension': dimension,
                'documents': [],
                'embeddings': [],
                'metadatas': [],
                'doc_ids': []
            }
            logger.info(f"📦 Created collection '{name}' with dimension {dimension}")
            return True
        return False
    
    async def add_documents(
        self,
        collection: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[DocumentMetadata]
    ) -> bool:
        """Add documents to collection"""
        if collection not in self.collections:
            logger.error(f"❌ Collection '{collection}' does not exist")
            return False
        
        coll = self.collections[collection]
        
        for doc, embedding, metadata in zip(documents, embeddings, metadatas):
            coll['documents'].append(doc)
            coll['embeddings'].append(embedding)
            coll['metadatas'].append(metadata)
            coll['doc_ids'].append(metadata.doc_id)
        
        logger.info(f"✅ Added {len(documents)} documents to '{collection}'")
        return True
    
    async def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search for similar documents using cosine similarity"""
        if collection not in self.collections:
            logger.warning(f"⚠️  Collection '{collection}' does not exist")
            return []
        
        coll = self.collections[collection]
        
        if not coll['embeddings']:
            logger.warning(f"⚠️  No documents in collection '{collection}'")
            return []
        
        # Calculate cosine similarities
        query_vec = np.array(query_embedding)
        similarities = []
        
        for idx, emb in enumerate(coll['embeddings']):
            emb_vec = np.array(emb)
            # Cosine similarity
            similarity = np.dot(query_vec, emb_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(emb_vec) + 1e-10
            )
            
            # Apply metadata filter if provided
            if filter_metadata:
                metadata = coll['metadatas'][idx]
                match = all(
                    getattr(metadata, key, None) == value
                    for key, value in filter_metadata.items()
                )
                if not match:
                    continue
            
            similarities.append((idx, float(similarity)))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results
        results = []
        for idx, score in similarities[:top_k]:
            result = VectorSearchResult(
                doc_id=coll['doc_ids'][idx],
                content=coll['documents'][idx],
                metadata=coll['metadatas'][idx],
                score=score,
                embedding=coll['embeddings'][idx]
            )
            results.append(result)
        
        logger.info(f"🔍 Found {len(results)} results for query in '{collection}'")
        return results
    
    async def delete_documents(
        self,
        collection: str,
        doc_ids: List[str]
    ) -> bool:
        """Delete documents by ID"""
        if collection not in self.collections:
            return False
        
        coll = self.collections[collection]
        indices_to_remove = []
        
        for doc_id in doc_ids:
            if doc_id in coll['doc_ids']:
                idx = coll['doc_ids'].index(doc_id)
                indices_to_remove.append(idx)
        
        # Remove in reverse order to maintain indices
        for idx in sorted(indices_to_remove, reverse=True):
            del coll['documents'][idx]
            del coll['embeddings'][idx]
            del coll['metadatas'][idx]
            del coll['doc_ids'][idx]
        
        logger.info(f"🗑️  Deleted {len(indices_to_remove)} documents from '{collection}'")
        return True
    
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics"""
        if collection not in self.collections:
            return {}
        
        coll = self.collections[collection]
        return {
            'name': collection,
            'count': len(coll['documents']),
            'dimension': coll['dimension'],
            'provider': 'in-memory'
        }
    
    async def list_collections(self) -> List[str]:
        """List all collection names"""
        return list(self.collections.keys())
    
    async def health_check(self) -> bool:
        """Health check"""
        return self.initialized
