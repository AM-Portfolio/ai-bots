"""
Parser Registry for Multi-Language Code Chunking

Automatically selects the appropriate parser based on file extension
and provides a unified interface for code chunking across 10+ languages.
"""

from pathlib import Path
from typing import Dict, List, Optional
import logging

from .base_parser import BaseParser, CodeChunk

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Central registry for language parsers.
    
    Automatically selects the right parser based on file extension
    and falls back to simple chunking for unsupported languages.
    """
    
    def __init__(self):
        """Initialize with empty registry"""
        self._parsers: Dict[str, BaseParser] = {}
        self._extension_map: Dict[str, str] = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """Register all available parsers"""
        try:
            from .python_parser import PythonParser
            self.register('python', PythonParser())
        except ImportError as e:
            logger.warning(f"Failed to load PythonParser: {e}")
        
        try:
            from .js_parser import JavaScriptParser
            self.register('javascript', JavaScriptParser())
        except ImportError as e:
            logger.warning(f"Failed to load JavaScriptParser: {e}")
        
        try:
            from .java_parser import JavaParser
            self.register('java', JavaParser())
        except ImportError as e:
            logger.warning(f"Failed to load JavaParser: {e}")
        
        try:
            from .cpp_parser import CppParser
            self.register('cpp', CppParser())
        except ImportError as e:
            logger.warning(f"Failed to load CppParser: {e}")
        
        try:
            from .kotlin_parser import KotlinParser
            self.register('kotlin', KotlinParser())
        except ImportError as e:
            logger.warning(f"Failed to load KotlinParser: {e}")
        
        try:
            from .dart_parser import DartParser
            self.register('dart', DartParser())
        except ImportError as e:
            logger.warning(f"Failed to load DartParser: {e}")
        
        # Always register fallback parser
        from .fallback_parser import FallbackParser
        self._fallback_parser = FallbackParser()
        
        logger.info(f"✅ Registered {len(self._parsers)} language parsers")
    
    def register(self, language: str, parser: BaseParser):
        """
        Register a parser for a language.
        
        Args:
            language: Language identifier (e.g., 'python')
            parser: Parser instance
        """
        self._parsers[language] = parser
        
        # Map file extensions to language
        for ext in parser.get_file_extension():
            self._extension_map[ext.lower()] = language
        
        logger.debug(f"Registered {language} parser for {parser.get_file_extension()}")
    
    def get_parser(self, file_path: str) -> BaseParser:
        """
        Get appropriate parser for a file.
        
        Args:
            file_path: Path to source file
            
        Returns:
            Parser instance (falls back to FallbackParser if unsupported)
        """
        file_ext = Path(file_path).suffix.lower()
        
        # Check if we have a parser for this extension
        language = self._extension_map.get(file_ext)
        if language and language in self._parsers:
            return self._parsers[language]
        
        # Fallback to generic parser
        logger.debug(f"No specific parser for {file_ext}, using fallback")
        return self._fallback_parser
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """
        Parse a file using the appropriate parser.
        
        Args:
            file_path: Path to source file
            
        Returns:
            List of CodeChunk objects
        """
        parser = self.get_parser(file_path)
        return parser.parse_file(file_path)
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of all supported file extensions"""
        return list(self._extension_map.keys())
    
    def get_supported_languages(self) -> List[str]:
        """Get list of all supported languages"""
        return list(self._parsers.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """Check if a file extension is supported"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self._extension_map or file_ext in [
            '.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html', '.css'
        ]


# Global registry instance
parser_registry = ParserRegistry()


__all__ = [
    'ParserRegistry',
    'parser_registry',
    'BaseParser',
    'CodeChunk'
]
