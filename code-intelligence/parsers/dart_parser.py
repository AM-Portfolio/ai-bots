"""Dart parser for Flutter apps"""

from typing import List
import logging
from .base_parser import BaseParser, CodeChunk
from .fallback_parser import FallbackParser

logger = logging.getLogger(__name__)


class DartParser(BaseParser):
    """Dart parser for Flutter (uses fallback for now, tree-sitter ready)"""
    
    def get_language(self) -> str:
        return "dart"
    
    def get_file_extension(self) -> List[str]:
        return ['.dart']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse Dart file"""
        fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
        return fallback.parse_file(file_path)
