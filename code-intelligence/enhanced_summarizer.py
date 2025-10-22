"""
Enhanced Code Summarizer - Simplified orchestrator for code summarization

Delegates to specialized modules:
- MetadataExtractor: Extracts imports, exceptions, annotations, etc.
- FileTypeDetector: Detects special file types
- PromptBuilder: Builds enhanced prompts
- FallbackSummarizer: Generates summaries without AI
- SummaryBatcher: Handles batch processing
"""

import asyncio
from typing import Optional, Dict, List, Any
import logging

from parsers.base_parser import CodeChunk
from storage.repo_state import RepoState
from utils.rate_limiter import RateLimitController, QuotaType
from utils.summary_batcher import SummaryBatcher
from utils.metadata_extractor import MetadataExtractor
from utils.file_type_detector import FileTypeDetector
from utils.prompt_builder import PromptBuilder
from utils.fallback_summarizer import FallbackSummarizer

logger = logging.getLogger(__name__)


class EnhancedCodeSummarizer:
    """
    Simplified summarizer orchestrator.
    
    Delegates to specialized modules:
    - MetadataExtractor: Extract code metadata
    - FileTypeDetector: Detect file types
    - PromptBuilder: Build prompts
    - FallbackSummarizer: Generate fallback summaries
    - SummaryBatcher: Handle batch processing
    """
    
    def __init__(
        self,
        repo_state: RepoState,
        rate_limiter: RateLimitController,
        azure_client=None,
        batch_size: int = 10
    ):
        self.repo_state = repo_state
        self.rate_limiter = rate_limiter
        self.azure_client = azure_client
        
        # Initialize specialized modules
        self.metadata_extractor = MetadataExtractor()
        self.file_type_detector = FileTypeDetector()
        self.prompt_builder = PromptBuilder()
        self.fallback_summarizer = FallbackSummarizer()
        self.batcher = SummaryBatcher(batch_size=batch_size)
        
        if self.azure_client is None:
            self._init_azure_client()
    
    def _init_azure_client(self):
        """Initialize Azure OpenAI client"""
        try:
            from shared.azure_services.azure_ai_manager import azure_ai_manager
            if azure_ai_manager.models.is_available():
                self.azure_client = azure_ai_manager.models
                logger.info("✅ Using Azure OpenAI for enhanced summarization")
            else:
                logger.warning("Azure OpenAI not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
    
    def extract_metadata(self, chunk: CodeChunk) -> Dict[str, Any]:
        """Extract rich metadata from code chunk (delegates to MetadataExtractor)"""
        return self.metadata_extractor.extract_metadata(
            chunk.content,
            chunk.metadata.language
        )
    
    async def summarize_chunk(
        self,
        chunk: CodeChunk,
        use_cache: bool = True
    ) -> str:
        """Generate enhanced summary with technical and business context"""
        
        # Check cache
        if use_cache:
            cached = self.repo_state.get_cached_summary(chunk.chunk_id)
            if cached:
                logger.debug(f"Cache hit for {chunk.chunk_id}")
                return cached
        
        # Extract metadata using MetadataExtractor
        metadata = self.extract_metadata(chunk)
        
        # Generate enhanced summary
        try:
            summary = await self._generate_summary_with_llm(chunk, metadata)
            
            # Update cache
            self.repo_state.update_chunk_state(
                chunk_id=chunk.chunk_id,
                file_path=chunk.metadata.file_path,
                chunk_content=chunk.content,
                chunk_index=int(chunk.chunk_id.split('_')[-1]) if '_' in chunk.chunk_id else 0,
                summary=summary,
                status="summarized"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize {chunk.chunk_id}: {e}")
            return self.fallback_summarizer.generate_summary(chunk, metadata)
    
    async def _generate_summary_with_llm(
        self,
        chunk: CodeChunk,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate summary using Azure GPT-4o mini"""
        if not self.azure_client:
            logger.debug(f"No Azure client, using fallback for {chunk.chunk_id}")
            return self.fallback_summarizer.generate_summary(chunk, metadata)
        
        # Detect file type and build prompt
        file_type = self.file_type_detector.detect_file_type(
            chunk.metadata.file_path,
            chunk.content
        )
        prompt = self.prompt_builder.build_prompt(chunk, metadata, file_type)
        
        # Log summarization details
        logger.debug(f"📝 Summarizing {chunk.chunk_id}")
        logger.debug(f"   File: {chunk.metadata.file_path}")
        logger.debug(f"   Type: {chunk.metadata.chunk_type}")
        logger.debug(f"   Symbol: {chunk.metadata.symbol_name or 'N/A'}")
        logger.debug(f"   Lines: {chunk.metadata.start_line}-{chunk.metadata.end_line}")
        logger.debug(f"   Prompt length: {len(prompt)} chars")
        logger.debug(f"   Metadata: imports={len(metadata.get('imports', []))}, "
                    f"exceptions={len(metadata.get('exceptions', []))}, "
                    f"annotations={len(metadata.get('annotations', []))}, "
                    f"env_vars={len(metadata.get('env_vars', []))}, "
                    f"endpoints={len(metadata.get('api_endpoints', []))}")
        
        # Call API with rate limiting
        async def call_api():
            logger.debug(f"   🔄 Calling Azure Chat Completion for {chunk.chunk_id}")
            response = await self.azure_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software architect analyzing code. Provide structured, technical summaries with business context, configurations, and error handling details."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4.1-mini",
                max_tokens=300,  # Increased for richer summaries
                temperature=0.2  # Lower for more factual
            )
            # Response is already a string, not a dict
            logger.debug(f"   ✅ Received summary for {chunk.chunk_id} ({len(response)} chars)")
            return response
        
        summary = await self.rate_limiter.submit(
            QuotaType.SUMMARIZATION,
            call_api,
            priority=3
        )
        
        return summary.strip() if summary else self.fallback_summarizer.generate_summary(chunk, metadata)
    
    async def summarize_batch(
        self,
        chunks: List[CodeChunk],
        use_cache: bool = True
    ) -> Dict[str, str]:
        """Summarize chunks in smaller batches with real-time progress tracking"""
        total_chunks = len(chunks)
        logger.info(f"📝 Starting batch summarization of {total_chunks} chunks")
        logger.info(f"   Cache enabled: {use_cache}")
        
        # Check cache
        chunks_to_process, cached_results = self.batcher.check_cache(
            items=chunks,
            cache_getter=lambda chunk: self.repo_state.get_chunk_state(chunk.chunk_id),
            use_cache=use_cache
        )
        
        # Process batches
        async def process_chunk(chunk: CodeChunk) -> str:
            try:
                return await self.summarize_chunk(chunk, use_cache)
            except Exception as e:
                metadata = self.extract_metadata(chunk)
                return self.fallback_summarizer.generate_summary(chunk, metadata)
        
        results, error_count, fallback_count = await self.batcher.process_batches(
            items=chunks_to_process,
            processor=process_chunk,
            total_count=total_chunks
        )
        
        # Merge cached and new results
        all_results = {**cached_results, **results}
        
        logger.info(f"   ✅ Batch complete: {len(all_results)} summaries generated (100.0%)")
        if error_count > 0:
            logger.warning(f"   ⚠️  {error_count} errors, {fallback_count} fallback summaries used")
        
        return all_results
