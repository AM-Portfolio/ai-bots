"""
ChromaDB Vector Database Provider
Production-ready vector database with persistence
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..base import VectorDBProvider, VectorSearchResult, DocumentMetadata

logger = logging.getLogger(__name__)


class ChromaDBProvider(VectorDBProvider):
    """ChromaDB-based vector database provider"""
    
    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        Initialize ChromaDB provider
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = None
        self.initialized = False
        logger.info(f"📚 ChromaDB Provider initializing with directory: {persist_directory}")
    
    async def initialize(self) -> bool:
        """Initialize ChromaDB client"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_directory
            ))
            
            self.initialized = True
            logger.info("✅ ChromaDB client initialized successfully")
            return True
            
        except ImportError:
            logger.warning("⚠️  ChromaDB not installed. Install with: pip install chromadb")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            return False
    
    async def create_collection(self, name: str, dimension: int) -> bool:
        """Create a new ChromaDB collection"""
        if not self.initialized:
            logger.error("❌ ChromaDB not initialized")
            return False
        
        try:
            self.client.create_collection(
                name=name,
                metadata={"dimension": dimension}
            )
            logger.info(f"📦 Created ChromaDB collection '{name}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {e}")
            return False
    
    async def add_documents(
        self,
        collection: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[DocumentMetadata]
    ) -> bool:
        """Add documents to ChromaDB collection"""
        if not self.initialized:
            return False
        
        try:
            coll = self.client.get_collection(collection)
            
            # Convert DocumentMetadata to dict for ChromaDB
            chroma_metadatas = []
            for meta in metadatas:
                chroma_meta = {
                    'source': meta.source,
                    'content_type': meta.content_type,
                    'doc_id': meta.doc_id
                }
                if meta.repo_name:
                    chroma_meta['repo_name'] = meta.repo_name
                if meta.file_path:
                    chroma_meta['file_path'] = meta.file_path
                if meta.language:
                    chroma_meta['language'] = meta.language
                    
                chroma_metadatas.append(chroma_meta)
            
            coll.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=chroma_metadatas,
                ids=[meta.doc_id for meta in metadatas]
            )
            
            logger.info(f"✅ Added {len(documents)} documents to ChromaDB '{collection}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            return False
    
    async def search(
        self,
        collection: str,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """Search ChromaDB collection"""
        if not self.initialized:
            return []
        
        try:
            coll = self.client.get_collection(collection)
            
            where_filter = filter_metadata if filter_metadata else None
            
            results = coll.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )
            
            search_results = []
            if results['ids'] and len(results['ids']) > 0:
                for idx in range(len(results['ids'][0])):
                    meta_dict = results['metadatas'][0][idx]
                    
                    metadata = DocumentMetadata(
                        doc_id=results['ids'][0][idx],
                        source=meta_dict.get('source', 'unknown'),
                        repo_name=meta_dict.get('repo_name'),
                        file_path=meta_dict.get('file_path'),
                        content_type=meta_dict.get('content_type', 'text'),
                        language=meta_dict.get('language')
                    )
                    
                    result = VectorSearchResult(
                        doc_id=results['ids'][0][idx],
                        content=results['documents'][0][idx],
                        metadata=metadata,
                        score=1.0 - results['distances'][0][idx],  # Convert distance to similarity
                        embedding=results['embeddings'][0][idx] if results.get('embeddings') else None
                    )
                    search_results.append(result)
            
            logger.info(f"🔍 Found {len(search_results)} results in ChromaDB '{collection}'")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def delete_documents(
        self,
        collection: str,
        doc_ids: List[str]
    ) -> bool:
        """Delete documents from ChromaDB"""
        if not self.initialized:
            return False
        
        try:
            coll = self.client.get_collection(collection)
            coll.delete(ids=doc_ids)
            logger.info(f"🗑️  Deleted {len(doc_ids)} documents from ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"❌ Delete failed: {e}")
            return False
    
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get ChromaDB collection statistics"""
        if not self.initialized:
            return {}
        
        try:
            coll = self.client.get_collection(collection)
            count = coll.count()
            
            return {
                'name': collection,
                'count': count,
                'provider': 'chromadb',
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
    
    async def health_check(self) -> bool:
        """Check ChromaDB health"""
        return self.initialized and self.client is not None
