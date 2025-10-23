"""
Fallback Summarizer - Generates summaries without AI
"""
from pathlib import Path
from typing import Dict, Any
import logging

from parsers.base_parser import CodeChunk

logger = logging.getLogger(__name__)


class FallbackSummarizer:
    """Generates rich fallback summaries without AI"""
    
    def generate_summary(self, chunk: CodeChunk, metadata: Dict[str, Any]) -> str:
        """
        Generate rich fallback summary without AI.
        
        Args:
            chunk: Code chunk
            metadata: Extracted metadata
            
        Returns:
            Formatted summary string
        """
        meta = chunk.metadata
        parts = []
        
        # Basic info
        if meta.symbol_name:
            parts.append(f"**{meta.chunk_type}** `{meta.symbol_name}` in {Path(meta.file_path).name}")
        else:
            parts.append(f"**{meta.chunk_type}** in {Path(meta.file_path).name} (lines {meta.start_line}-{meta.end_line})")
        
        # Add metadata insights
        if metadata['imports']:
            parts.append(f"Dependencies: {', '.join(metadata['imports'][:3])}")
        
        if metadata['exceptions']:
            parts.append(f"Handles: {', '.join(metadata['exceptions'])}")
        
        if metadata['annotations']:
            parts.append(f"Annotations: {', '.join(metadata['annotations'][:3])}")
        
        if metadata['env_vars']:
            parts.append(f"Uses env: {', '.join(metadata['env_vars'][:3])}")
        
        if metadata['api_endpoints']:
            parts.append(f"Endpoints: {', '.join(metadata['api_endpoints'][:2])}")
        
        return " | ".join(parts)
