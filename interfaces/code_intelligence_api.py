"""
Code Intelligence API for Enhanced Embedding and Querying

Integrates the code intelligence pipeline with the main application's
vector database system, enabling rich technical summaries to be embedded
and queried alongside code.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import sys
from pathlib import Path

# Add code-intelligence to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code-intelligence"))

from rate_limiter import RateLimitController, QuotaType
from repo_state import RepoState
from parsers import parser_registry
from change_planner import ChangePlanner
from enhanced_summarizer import EnhancedCodeSummarizer
from vector_store import VectorStore, EmbeddingPoint

from shared.logger import get_logger
from shared.azure_services.azure_ai_manager import azure_ai_manager

logger = get_logger(__name__)

router = APIRouter(prefix="/api/code-intelligence", tags=["code-intelligence"])


class EmbedRepoRequest(BaseModel):
    repo_path: str = "."
    max_files: Optional[int] = None
    force_reindex: bool = False
    collection_name: str = "code_intelligence"


class EmbedRepoResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    message: str


class QueryCodeRequest(BaseModel):
    query: str
    limit: int = 10
    collection_name: str = "code_intelligence"
    filters: Optional[Dict[str, Any]] = None


class QueryCodeResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    query: str
    total_results: int


class CodeIntelligenceOrchestrator:
    """
    Orchestrator for code intelligence operations.
    Integrates with the main app's Azure AI and vector DB systems.
    """
    
    def __init__(self):
        self.rate_limiter = None
        self.summarizer = None
        self.vector_store = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the orchestrator with app's Azure AI"""
        if self._initialized:
            return
        
        try:
            logger.info("🚀 Initializing Code Intelligence Orchestrator...")
            
            # Initialize rate limiter
            self.rate_limiter = RateLimitController()
            await self.rate_limiter.start()
            
            # Initialize repo state
            self.repo_state = RepoState(".code-intelligence-state.json")
            
            # Initialize enhanced summarizer with app's Azure AI
            self.summarizer = EnhancedCodeSummarizer(
                self.repo_state,
                self.rate_limiter,
                azure_ai_manager.models if azure_ai_manager.models.is_available() else None
            )
            
            # Initialize vector store
            self.vector_store = VectorStore(
                collection_name="code_intelligence",
                qdrant_path="./qdrant_data"
            )
            
            self._initialized = True
            logger.info("✅ Code Intelligence Orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def embed_repository(
        self,
        repo_path: str = ".",
        max_files: Optional[int] = None,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Embed repository with enhanced summaries.
        
        Args:
            repo_path: Path to repository
            max_files: Maximum files to process
            force_reindex: Force re-embedding of all files
            
        Returns:
            Statistics about the embedding process
        """
        await self.initialize()
        
        logger.info(f"📖 Starting code intelligence embedding for: {repo_path}")
        
        # Initialize change planner
        change_planner = ChangePlanner(repo_path)
        
        # Discover files
        all_files = self._discover_files(repo_path)
        logger.info(f"📁 Discovered {len(all_files)} files")
        
        # Detect changes
        if force_reindex:
            changed_files = set(all_files)
            logger.info("🔄 Force reindex enabled - processing all files")
        else:
            changed_files = self.repo_state.get_changed_files(all_files)
            logger.info(f"📊 {len(changed_files)} files changed")
        
        # Prioritize files
        prioritized_files = change_planner.get_top_priority_files(
            all_files,
            max_files=max_files or len(all_files),
            changed_files=changed_files
        )
        
        # Parse and chunk
        all_chunks = []
        for file_path in prioritized_files:
            try:
                chunks = parser_registry.parse_file(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
        
        logger.info(f"✂️ Generated {len(all_chunks)} code chunks")
        
        # Generate enhanced summaries
        logger.info("📝 Generating enhanced summaries...")
        summaries = await self.summarizer.summarize_batch(all_chunks)
        
        # Generate embeddings (code + summary)
        logger.info("🔢 Generating embeddings...")
        embeddings = await self._embed_batch(all_chunks, summaries)
        
        # Store in vector DB
        logger.info("💾 Storing in vector database...")
        embedding_points = [
            EmbeddingPoint(
                chunk_id=chunk.chunk_id,
                embedding=embeddings[i],
                content=chunk.content,
                summary=summaries.get(chunk.chunk_id, ""),
                metadata={
                    "file_path": chunk.metadata.file_path,
                    "language": chunk.metadata.language,
                    "chunk_type": chunk.metadata.chunk_type,
                    "symbol_name": chunk.metadata.symbol_name,
                    "start_line": chunk.metadata.start_line,
                    "end_line": chunk.metadata.end_line,
                    "token_count": chunk.metadata.token_count
                }
            )
            for i, chunk in enumerate(all_chunks)
            if i < len(embeddings)
        ]
        
        upsert_result = await self.vector_store.upsert_batch(embedding_points)
        
        # Update repo state
        for file_path in prioritized_files:
            file_chunks = [c for c in all_chunks if c.metadata.file_path == file_path]
            if file_chunks:
                self.repo_state.update_file_state(
                    file_path=file_path,
                    language=file_chunks[0].metadata.language,
                    chunk_count=len(file_chunks),
                    status="completed"
                )
        
        self.repo_state.save_manifest()
        
        # Return statistics
        stats = {
            "files_discovered": len(all_files),
            "files_changed": len(changed_files),
            "files_processed": len(prioritized_files),
            "chunks_generated": len(all_chunks),
            "chunks_embedded": upsert_result["successful"],
            "chunks_failed": upsert_result["failed"],
            "success_rate": upsert_result["success_rate"],
        }
        
        logger.info(f"✅ Embedding complete: {stats['chunks_embedded']}/{stats['chunks_generated']} chunks")
        
        return stats
    
    async def _embed_batch(
        self,
        chunks: List,
        summaries: Dict[str, str]
    ) -> List[List[float]]:
        """Generate embeddings for chunks with summaries"""
        embeddings = []
        batch_size = self.rate_limiter.get_adaptive_batch_size(QuotaType.EMBEDDING)
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare texts (summary + code for rich context)
            texts = [
                f"Summary: {summaries.get(chunk.chunk_id, '')}\n\nCode:\n{chunk.content[:2000]}"
                for chunk in batch
            ]
            
            # Embed with rate limiting
            async def embed_batch():
                if not azure_ai_manager.models.is_available():
                    raise Exception("Azure OpenAI not configured")
                
                response = await azure_ai_manager.models.create_embeddings(
                    texts=texts,
                    model="text-embedding-3-large"
                )
                return [item["embedding"] for item in response]
            
            try:
                batch_embeddings = await self.rate_limiter.submit(
                    QuotaType.EMBEDDING,
                    embed_batch,
                    priority=2
                )
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to embed batch: {e}")
                # Add placeholder embeddings
                embeddings.extend([[0.0] * 3072] * len(batch))
        
        return embeddings
    
    def _discover_files(self, repo_path: str) -> List[str]:
        """Discover code files in repository"""
        import os
        from pathlib import Path
        
        exclude_patterns = [
            '.git', 'node_modules', '__pycache__', 'venv',
            '.venv', 'dist', 'build', '.next', 'target'
        ]
        
        files = []
        supported_extensions = parser_registry.get_supported_extensions()
        
        for root, dirs, filenames in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_patterns]
            
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(str(file_path.relative_to(repo_path)))
        
        return files
    
    async def query_code(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query code using semantic search.
        
        Args:
            query: Natural language query
            limit: Maximum results
            filters: Metadata filters (language, file_path, etc.)
            
        Returns:
            List of matching code chunks with summaries
        """
        await self.initialize()
        
        # Generate query embedding
        query_embedding = await self._embed_query(query)
        
        # Search vector DB
        results = self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            filter_dict=filters
        )
        
        return results
    
    async def _embed_query(self, query: str) -> List[float]:
        """Generate embedding for query"""
        async def embed():
            response = await azure_ai_manager.models.create_embeddings(
                texts=[query],
                model="text-embedding-3-large"
            )
            return response[0]["embedding"]
        
        return await self.rate_limiter.submit(
            QuotaType.EMBEDDING,
            embed,
            priority=1  # High priority for queries
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.rate_limiter:
            await self.rate_limiter.stop()


# Global orchestrator instance
orchestrator = CodeIntelligenceOrchestrator()


@router.post("/embed", response_model=EmbedRepoResponse)
async def embed_repository(request: EmbedRepoRequest):
    """
    Embed a repository with enhanced summaries.
    
    This endpoint:
    1. Discovers and prioritizes code files
    2. Generates rich technical summaries
    3. Embeds code + summaries together
    4. Stores in vector database
    """
    try:
        stats = await orchestrator.embed_repository(
            repo_path=request.repo_path,
            max_files=request.max_files,
            force_reindex=request.force_reindex
        )
        
        return EmbedRepoResponse(
            success=True,
            stats=stats,
            message=f"Successfully embedded {stats['chunks_embedded']} code chunks"
        )
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryCodeResponse)
async def query_code(request: QueryCodeRequest):
    """
    Query code using semantic search.
    
    Searches across:
    - Enhanced technical summaries
    - Code content
    - Metadata (language, file paths, etc.)
    """
    try:
        results = await orchestrator.query_code(
            query=request.query,
            limit=request.limit,
            filters=request.filters
        )
        
        return QueryCodeResponse(
            success=True,
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get code intelligence system status"""
    try:
        await orchestrator.initialize()
        
        collection_info = orchestrator.vector_store.get_collection_info()
        repo_stats = orchestrator.repo_state.get_stats()
        
        return {
            "status": "ready",
            "vector_db": collection_info,
            "repository": repo_stats,
            "supported_languages": parser_registry.get_supported_languages(),
            "supported_extensions": parser_registry.get_supported_extensions()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await orchestrator.initialize()
        is_healthy = orchestrator.vector_store.health_check()
        
        return {
            "healthy": is_healthy,
            "azure_openai": azure_ai_manager.models.is_available(),
            "vector_db": is_healthy
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }
