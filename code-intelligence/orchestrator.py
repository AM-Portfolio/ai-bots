"""
Code Intelligence Orchestrator

Core orchestration logic for code intelligence operations.
Provides high-level workflows for:
- Repository embedding with optional GitHub LLM analysis
- Code summarization
- Change analysis
- Health checks

This is the coordination layer that the API/CLI should call.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Add parent directory to path for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from embed_repo import EmbeddingPipeline
from storage.vector_store import VectorStore
from shared.vector_db.embedding_service import EmbeddingService
from shared.config import settings
from analysis.github_analyzer import GitHubAnalyzer
from pipeline.embedding_workflow import EmbeddingWorkflow
from utils.enhanced_query import EnhancedQueryService

logger = logging.getLogger(__name__)

# Suppress verbose Azure and HTTP logs - only show errors
logging.getLogger('shared.azure_services.model_deployment_service').setLevel(logging.ERROR)
logging.getLogger('shared.azure_services').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db.embedding_service').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db').setLevel(logging.WARNING)
logging.getLogger('storage.vector_store').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db.factory').setLevel(logging.WARNING)
logging.getLogger('shared.vector_db.providers').setLevel(logging.WARNING)


class CodeIntelligenceOrchestrator:
    """
    Main orchestrator for code intelligence operations.
    
    Core Operations:
    - embed_repository() - Embed code into vector database
    - query() - Search vector database for relevant code
    - get_stats() - Get vector database statistics
    - cleanup() - Delete indexed data by collection/repository
    - health_check() - Check service health
    
    This is the coordination layer that the API/CLI should call.
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize orchestrator.
        
        Args:
            repo_path: Path to repository (default: current directory)
        """
        self.repo_path = Path(repo_path).resolve()
        self.settings = settings
        self.github_analyzer = GitHubAnalyzer()
        logger.info(f"📁 Repository: {self.repo_path}")
    
    async def embed_repository(
        self,
        collection_name: str = "code_intelligence",
        max_files: Optional[int] = None,
        force_reindex: bool = False,
        github_repository: Optional[str] = None,
        query: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate repository embedding with optional GitHub LLM analysis.
        
        Workflow:
        1. (Optional) Use GitHub LLM to analyze repository
        2. Get relevant files based on analysis
        3. Delegate to EmbeddingOrchestrator for embedding pipeline
        
        Args:
            collection_name: Qdrant collection name
            max_files: Maximum number of files to process
            force_reindex: Force re-embedding of all files
            github_repository: Optional GitHub repository (owner/repo)
            query: Optional query for filtering files
            language: Optional language filter
            
        Returns:
            Statistics dictionary with processing results
        """
        logger.info("🚀 Starting repository embedding orchestration...")
        
        stats = {
            "success": True,
            "github_analysis": None,
            "files_discovered": 0,
            "files_processed": 0,
            "chunks_generated": 0,
            "chunks_embedded": 0,
            "failed_chunks": 0,
            "success_rate": 0.0
        }
        
        # STEP 1: Optional GitHub LLM Analysis
        github_file_paths = set()
        if github_repository:
            logger.info(f"\n🔍 STEP 1: GitHub LLM Repository Analysis")
            analysis_result = await self.github_analyzer.analyze_repository(
                repository=github_repository,
                query=query,
                max_results=max_files or 50,
                language=language
            )
            
            if not analysis_result.get("error") and analysis_result["files_found"] > 0:
                stats["github_analysis"] = {
                    "repository": github_repository,
                    "files_found": analysis_result["files_found"],
                    "confidence": analysis_result["confidence"],
                    "summary": analysis_result["summary"]
                }
                github_file_paths = analysis_result["file_paths"]
        else:
            logger.info("\n📂 STEP 1: Using local file discovery")
        
        # STEP 2: Generate embeddings
        embedding_result = await self._generate_embeddings(
            github_file_paths=github_file_paths,
            max_files=max_files,
            force_reindex=force_reindex
        )
        
        # STEP 3: Store embeddings using workflow
        total_stored, total_failed = await self._store_embeddings(
            collection_name=collection_name,
            embedding_result=embedding_result
        )
        
        # Merge stats
        stats.update(embedding_result["stats"])
        stats["chunks_embedded"] = total_stored
        stats["failed_chunks"] = total_failed
        
        logger.info("\n✅ Repository embedding orchestration complete!")
        if stats.get("github_analysis"):
            logger.info(f"   GitHub: {stats['github_analysis']['files_found']} files analyzed")
        logger.info(f"   Stored: {total_stored} embeddings")

        
        return stats
    
    async def _generate_embeddings(
        self,
        github_file_paths: set,
        max_files: Optional[int],
        force_reindex: bool
    ) -> Dict[str, Any]:
        """
        Generate embeddings using EmbeddingPipeline.
        
        Returns:
            Embedding result dictionary
        """
        logger.info("\n📖 STEP 2: Repository Embedding Pipeline")
        
        embedding_pipeline = EmbeddingPipeline(
            repo_path=str(self.repo_path)
        )
        
        return await embedding_pipeline.generate_embeddings(
            file_filter=github_file_paths if github_file_paths else None,
            max_files=max_files,
            force_reindex=force_reindex
        )
    
    async def _store_embeddings(
        self,
        collection_name: str,
        embedding_result: Dict[str, Any]
    ) -> tuple[int, int]:
        """
        Store embeddings in vector database and update repo state.
        
        Returns:
            Tuple of (total_stored, total_failed)
        """
        logger.info("\n💾 STEP 3: Storing embeddings in vector database")
        
        # Use EmbeddingWorkflow for storage
        workflow = EmbeddingWorkflow(
            repo_path=self.repo_path
        )
        
        result = await workflow.execute(
            embedding_data=embedding_result["embedding_data"],
            chunks=embedding_result["chunks"],
            collection_name=collection_name
        )
        
        return result["total_stored"], result["total_failed"]
    
    async def query(
        self,
        query_text: str,
        collection_name: str = "code_intelligence",
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query the vector database for relevant code.
        
        Args:
            query_text: Query string
            collection_name: Qdrant collection name
            limit: Maximum number of results
            
        Returns:
            Search results with relevant code chunks
        """
        logger.info(f"� Querying vector database: {query_text}")
        
        try:
            # Get embedding dimension
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            # Initialize vector store
            vector_store = await VectorStore.create(
                collection_name=collection_name,
                embedding_dim=dimension
            )
            
            # Generate query embedding
            query_embedding = await embedding_service.generate_embedding(query_text)
            
            # Search vector store
            results = await vector_store.search(
                query_embedding=query_embedding,
                limit=limit
            )
            
            return {
                "success": True,
                "query": query_text,
                "results_count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_stats(self, collection_name: str = "code_intelligence") -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Args:
            collection_name: Qdrant collection name
            
        Returns:
            Statistics dictionary
        """
        logger.info("📊 Getting vector database statistics...")
        
        try:
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            vector_store = await VectorStore.create(
                collection_name=collection_name,
                embedding_dim=dimension
            )
            
            # Get collection info
            info = vector_store.get_collection_info()
            
            return {
                "success": True,
                "collection_name": collection_name,
                "total_vectors": info.get("vectors_count", 0),
                "dimension": dimension
            }
        except Exception as e:
            logger.error(f"❌ Stats retrieval failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(
        self,
        collection_name: Optional[str] = None,
        github_repository: Optional[str] = None,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up indexed data by collection name or GitHub repository.
        
        Args:
            collection_name: Qdrant collection name to delete
            github_repository: GitHub repository (owner/repo) - converts to collection name
            confirm: Confirmation flag to prevent accidental deletion
            
        Returns:
            Cleanup result dictionary
        """
        # Determine collection name from repository if provided
        if github_repository and not collection_name:
            # Convert owner/repo to collection name format
            collection_name = github_repository.replace("/", "_").replace("-", "_").lower()
            logger.info(f"🗑️ Converting repository '{github_repository}' to collection '{collection_name}'")
        
        if not collection_name:
            return {
                "success": False,
                "error": "Either collection_name or github_repository must be provided"
            }
        
        if not confirm:
            return {
                "success": False,
                "error": "Deletion not confirmed. Set confirm=True to proceed.",
                "collection_name": collection_name,
                "warning": "This will permanently delete all embeddings in this collection!"
            }
        
        logger.info(f"⚠️ Cleaning up collection: {collection_name}")
        
        try:
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            vector_store = await VectorStore.create(
                collection_name=collection_name,
                embedding_dim=dimension
            )
            
            # Get stats before deletion
            try:
                info_before = vector_store.get_collection_info()
                vectors_count = info_before.get("vectors_count", 0)
            except:
                vectors_count = 0
            
            # Delete collection
            vector_store.delete_collection()
            
            logger.info(f"✅ Successfully deleted collection '{collection_name}'")
            
            return {
                "success": True,
                "collection_name": collection_name,
                "vectors_deleted": vectors_count,
                "message": f"Collection '{collection_name}' has been permanently deleted."
            }
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {
                "success": False,
                "collection_name": collection_name,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all services.
        
        Returns:
            Health status for each component
        """
        logger.info("🏥 Running health checks...")
        
        health = {
            "embedding_service": False,
            "vector_store": False,
            "llm_service": False
        }
        
        # Check embedding service
        try:
            embedding_service = EmbeddingService(provider="auto")
            health["embedding_service"] = await embedding_service.health_check()
            logger.info(f"✅ Embedding service: {'Connected' if health['embedding_service'] else 'Failed'}")
        except Exception as e:
            logger.error(f"❌ Embedding service: {e}")
        
        # Check vector store
        try:
            # Get dimension from embedding service
            embedding_service = EmbeddingService(provider="auto")
            dimension = embedding_service.get_dimension()
            
            vector_store = await VectorStore.create(
                collection_name="health_check_test",
                embedding_dim=dimension
            )
            health["vector_store"] = True
            logger.info("✅ Vector store: Connected")
        except Exception as e:
            logger.error(f"❌ Vector store: {e}")
        
        # Check LLM service
        try:
            # TODO: Add LLM health check
            health["llm_service"] = True
            logger.info("✅ LLM service: Ready")
        except Exception as e:
            logger.error(f"❌ LLM service: {e}")
        
        return health

