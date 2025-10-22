"""Kotlin parser with tree-sitter support"""

from typing import List
import logging
from .base_parser import BaseParser, CodeChunk
from .fallback_parser import FallbackParser

logger = logging.getLogger(__name__)


class KotlinParser(BaseParser):
    """Kotlin parser (uses fallback for now, tree-sitter ready)"""
    
    def get_language(self) -> str:
        return "kotlin"
    
    def get_file_extension(self) -> List[str]:
        return ['.kt', '.kts']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse Kotlin file"""
        fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
        return fallback.parse_file(file_path)
