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
    embedding_type: Optional[str] = "both"  # "code", "summary", or "both"


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
        
        # Generate TWO embeddings per chunk (code + summary)
        logger.info("🔢 Generating dual embeddings (raw code + enhanced summary)...")
        code_embeddings, summary_embeddings = await self._embed_batch(all_chunks, summaries)
        
        # Store BOTH embeddings in vector DB
        logger.info("💾 Storing in vector database...")
        
        # Create TWO embedding points per chunk
        embedding_points = []
        
        for i, chunk in enumerate(all_chunks):
            if i >= len(code_embeddings):
                continue
            
            base_metadata = {
                "file_path": chunk.metadata.file_path,
                "language": chunk.metadata.language,
                "chunk_type": chunk.metadata.chunk_type,
                "symbol_name": chunk.metadata.symbol_name,
                "start_line": chunk.metadata.start_line,
                "end_line": chunk.metadata.end_line,
                "token_count": chunk.metadata.token_count
            }
            
            # 1. Raw code embedding
            embedding_points.append(
                EmbeddingPoint(
                    chunk_id=f"{chunk.chunk_id}_code",
                    embedding=code_embeddings[i],
                    content=chunk.content,
                    summary="",  # No summary for raw code embedding
                    metadata={
                        **base_metadata,
                        "embedding_type": "raw_code",
                        "parent_chunk_id": chunk.chunk_id
                    }
                )
            )
            
            # 2. Enhanced summary embedding
            embedding_points.append(
                EmbeddingPoint(
                    chunk_id=f"{chunk.chunk_id}_summary",
                    embedding=summary_embeddings[i],
                    content=chunk.content,
                    summary=summaries.get(chunk.chunk_id, ""),
                    metadata={
                        **base_metadata,
                        "embedding_type": "enhanced_summary",
                        "parent_chunk_id": chunk.chunk_id
                    }
                )
            )
        
        logger.info(f"📊 Created {len(embedding_points)} embedding points ({len(embedding_points)//2} code + {len(embedding_points)//2} summaries)")
        
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
    ) -> tuple[List[List[float]], List[List[float]]]:
        """
        Generate TWO embeddings per chunk:
        1. Raw code embedding - for exact code matching
        2. Enhanced summary embedding - for conceptual/technical understanding
        
        Returns:
            Tuple of (code_embeddings, summary_embeddings)
        """
        code_embeddings = []
        summary_embeddings = []
        batch_size = self.rate_limiter.get_adaptive_batch_size(QuotaType.EMBEDDING)
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare TWO sets of texts
            # 1. Raw code only (for exact matching)
            code_texts = [chunk.content[:2000] for chunk in batch]
            
            # 2. Enhanced summary with context (for conceptual search)
            summary_texts = [
                f"Summary: {summaries.get(chunk.chunk_id, '')}\n\nCode Context:\n{chunk.content[:500]}"
                for chunk in batch
            ]
            
            # Embed raw code
            async def embed_code():
                if not azure_ai_manager.models.is_available():
                    raise Exception("Azure OpenAI not configured")
                
                response = await azure_ai_manager.models.create_embeddings(
                    texts=code_texts,
                    model="text-embedding-3-large"
                )
                return [item["embedding"] for item in response]
            
            # Embed enhanced summaries
            async def embed_summaries():
                if not azure_ai_manager.models.is_available():
                    raise Exception("Azure OpenAI not configured")
                
                response = await azure_ai_manager.models.create_embeddings(
                    texts=summary_texts,
                    model="text-embedding-3-large"
                )
                return [item["embedding"] for item in response]
            
            try:
                # Execute both embeddings in parallel
                code_batch, summary_batch = await asyncio.gather(
                    self.rate_limiter.submit(
                        QuotaType.EMBEDDING,
                        embed_code,
                        priority=2
                    ),
                    self.rate_limiter.submit(
                        QuotaType.EMBEDDING,
                        embed_summaries,
                        priority=2
                    )
                )
                
                code_embeddings.extend(code_batch)
                summary_embeddings.extend(summary_batch)
                
            except Exception as e:
                logger.error(f"Failed to embed batch: {e}")
                # Add placeholder embeddings
                code_embeddings.extend([[0.0] * 3072] * len(batch))
                summary_embeddings.extend([[0.0] * 3072] * len(batch))
        
        return code_embeddings, summary_embeddings
    
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
        filters: Optional[Dict[str, Any]] = None,
        embedding_type: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Query code using semantic search.
        
        Args:
            query: Natural language query
            limit: Maximum results
            filters: Metadata filters (language, file_path, etc.)
            embedding_type: Search "code", "summary", or "both" embeddings
            
        Returns:
            List of matching code chunks with summaries
        """
        await self.initialize()
        
        # Generate query embedding
        query_embedding = await self._embed_query(query)
        
        # Add embedding_type filter
        search_filters = filters.copy() if filters else {}
        
        if embedding_type == "code":
            search_filters["embedding_type"] = "raw_code"
        elif embedding_type == "summary":
            search_filters["embedding_type"] = "enhanced_summary"
        # "both" - no filter, search all
        
        # Search vector DB
        results = self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit * 2 if embedding_type == "both" else limit,  # Get more for deduplication
            filter_dict=search_filters
        )
        
        # If searching both, deduplicate by parent_chunk_id and merge
        if embedding_type == "both":
            results = self._merge_dual_results(results, limit)
        
        return results
    
    def _merge_dual_results(
        self,
        results: List[Dict[str, Any]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Merge results from both code and summary embeddings.
        For each chunk, combine scores from both embedding types.
        """
        chunk_map = {}
        
        for result in results:
            parent_id = result["metadata"].get("parent_chunk_id")
            if not parent_id:
                continue
            
            if parent_id not in chunk_map:
                chunk_map[parent_id] = {
                    "content": result["content"],
                    "summary": result.get("summary", ""),
                    "metadata": {k: v for k, v in result["metadata"].items() if k != "embedding_type"},
                    "code_score": 0.0,
                    "summary_score": 0.0,
                    "combined_score": 0.0
                }
            
            # Add score based on embedding type
            emb_type = result["metadata"].get("embedding_type")
            if emb_type == "raw_code":
                chunk_map[parent_id]["code_score"] = result.get("score", 0.0)
            elif emb_type == "enhanced_summary":
                chunk_map[parent_id]["summary_score"] = result.get("score", 0.0)
                # Use summary from summary embedding
                chunk_map[parent_id]["summary"] = result.get("summary", "")
        
        # Calculate combined score (weighted average: 40% code, 60% summary)
        for chunk_data in chunk_map.values():
            chunk_data["combined_score"] = (
                0.4 * chunk_data["code_score"] +
                0.6 * chunk_data["summary_score"]
            )
        
        # Sort by combined score and return top results
        merged_results = [
            {
                "content": data["content"],
                "summary": data["summary"],
                "metadata": data["metadata"],
                "score": data["combined_score"],
                "code_score": data["code_score"],
                "summary_score": data["summary_score"]
            }
            for data in chunk_map.values()
        ]
        
        merged_results.sort(key=lambda x: x["score"], reverse=True)
        return merged_results[:limit]
    
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
    Query code using semantic search with dual embeddings.
    
    Embedding Types:
    - "code": Search raw code embeddings (exact code matching)
    - "summary": Search enhanced summary embeddings (conceptual/technical)
    - "both": Search both and merge results (default, best for most queries)
    
    Searches across:
    - Raw code content (exact matching)
    - Enhanced technical summaries (conceptual understanding)
    - Metadata (language, file paths, symbols, etc.)
    """
    try:
        results = await orchestrator.query_code(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
            embedding_type=request.embedding_type
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
