"""
Base parser interface for tree-sitter code chunking.

All language-specific parsers inherit from BaseParser and implement
language-specific chunking strategies while maintaining consistent output.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a code chunk"""
    chunk_id: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, method, module, etc.
    symbol_name: Optional[str] = None
    parent_symbol: Optional[str] = None
    dependencies: List[str] = None
    token_count: int = 0
    content: str = ""
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class CodeChunk:
    """A chunk of code with metadata"""
    metadata: ChunkMetadata
    content: str
    
    @property
    def chunk_id(self) -> str:
        return self.metadata.chunk_id
    
    @property
    def token_count(self) -> int:
        return self.metadata.token_count


class BaseParser(ABC):
    """
    Base class for all language parsers.
    
    Subclasses must implement:
    - parse_file: Extract chunks from a file
    - get_language: Return language identifier
    """
    
    def __init__(self, target_chunk_tokens: int = 300, max_chunk_tokens: int = 400):
        """
        Initialize parser.
        
        Args:
            target_chunk_tokens: Target tokens per chunk (soft limit)
            max_chunk_tokens: Maximum tokens per chunk (hard limit)
        """
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
    
    @abstractmethod
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """
        Parse a file and extract code chunks.
        
        Args:
            file_path: Path to source file
            
        Returns:
            List of CodeChunk objects with metadata
        """
        pass
    
    @abstractmethod
    def get_language(self) -> str:
        """Return language identifier (e.g., 'python', 'javascript')"""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses simple heuristic: ~4 characters per token
        Override for more accurate language-specific estimation.
        """
        return len(text) // 4
    
    def should_skip_chunk(self, content: str, chunk_type: str = None) -> bool:
        """
        Determine if chunk should be skipped (too trivial to summarize).
        
        Skips:
        - Comments-only blocks
        - Simple getters/setters
        - Import-only statements
        - Trivial one-liners
        - Auto-generated code markers
        """
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        
        # Skip empty or very small chunks
        if len(lines) <= 1:
            return True
        
        # Count code lines (exclude comments, docstrings, imports)
        code_lines = 0
        in_docstring = False
        docstring_char = None
        
        for line in lines:
            # Track docstrings
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in line else "'''"
                    # Check if docstring closes on same line
                    if line.count(docstring_char) >= 2:
                        in_docstring = False
                elif docstring_char in line:
                    in_docstring = False
                continue
            
            if in_docstring:
                continue
            
            # Skip comments and imports
            if line.startswith('#') or line.startswith('import ') or line.startswith('from '):
                continue
            
            # Skip common language keywords that aren't real code
            if line in ['pass', 'return', 'return None', 'break', 'continue']:
                continue
            
            code_lines += 1
        
        # Skip if less than 3 lines of actual code
        if code_lines < 3:
            return True
        
        # Detect simple getters/setters (Python, Java, JS patterns)
        content_lower = content.lower()
        
        # Python property getters: just return self._attr
        if code_lines <= 3 and 'return self.' in content and '@property' in content:
            return True
        
        # Simple setters: just self.attr = value
        if code_lines <= 3 and 'self.' in content and '.setter' in content:
            return True
        
        # Java/C# getters: return this.field;
        if code_lines <= 3 and ('return this.' in content or 'return _' in content) and \
           ('get' in content_lower or 'getter' in content_lower):
            return True
        
        # Java/C# setters: this.field = value;
        if code_lines <= 3 and ('this.' in content or 'self.' in content) and \
           ('set' in content_lower or 'setter' in content_lower):
            return True
        
        # Auto-generated markers
        auto_markers = [
            '// auto-generated',
            '# auto-generated',
            '# generated by',
            '// generated by',
            '# do not edit',
            '// do not edit',
            '@generated'
        ]
        if any(marker in content_lower for marker in auto_markers):
            return True
        
        return False
    
    def create_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        file_name = Path(file_path).name
        return f"{file_name}:chunk_{chunk_index}"
    
    def should_split_chunk(self, content: str) -> bool:
        """Check if chunk exceeds token limits"""
        return self.estimate_tokens(content) > self.max_chunk_tokens
    
    def split_oversized_chunk(
        self,
        content: str,
        metadata: ChunkMetadata
    ) -> List[CodeChunk]:
        """
        Split a chunk that exceeds max_chunk_tokens.
        
        Default implementation: split by lines
        Override for smarter splitting strategies.
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for line in lines:
            line_tokens = self.estimate_tokens(line)
            
            if current_tokens + line_tokens > self.target_chunk_tokens and current_chunk:
                # Save current chunk
                chunk_content = '\n'.join(current_chunk)
                chunk_meta = ChunkMetadata(
                    chunk_id=f"{metadata.chunk_id}_part{chunk_index}",
                    file_path=metadata.file_path,
                    language=metadata.language,
                    start_line=metadata.start_line + chunk_index * len(current_chunk),
                    end_line=metadata.start_line + chunk_index * len(current_chunk) + len(current_chunk),
                    chunk_type=f"{metadata.chunk_type}_continuation",
                    symbol_name=metadata.symbol_name,
                    parent_symbol=metadata.parent_symbol,
                    token_count=current_tokens,
                    content=chunk_content
                )
                chunks.append(CodeChunk(metadata=chunk_meta, content=chunk_content))
                
                # Start new chunk
                current_chunk = [line]
                current_tokens = line_tokens
                chunk_index += 1
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunk_meta = ChunkMetadata(
                chunk_id=f"{metadata.chunk_id}_part{chunk_index}",
                file_path=metadata.file_path,
                language=metadata.language,
                start_line=metadata.start_line + chunk_index * len(current_chunk),
                end_line=metadata.end_line,
                chunk_type=f"{metadata.chunk_type}_continuation",
                symbol_name=metadata.symbol_name,
                parent_symbol=metadata.parent_symbol,
                token_count=current_tokens,
                content=chunk_content
            )
            chunks.append(CodeChunk(metadata=chunk_meta, content=chunk_content))
        
        return chunks
    
    def extract_dependencies(self, content: str) -> List[str]:
        """
        Extract import/dependency statements.
        
        Override in language-specific parsers for better accuracy.
        """
        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('import ', 'from ', 'require(', 'use ')):
                dependencies.append(line)
        return dependencies
    
    def get_file_extension(self) -> List[str]:
        """
        Return list of file extensions this parser handles.
        
        Example: ['.py', '.pyw'] for Python
        """
        return []
    
    def supports_file(self, file_path: str) -> bool:
        """Check if this parser supports a given file"""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.get_file_extension()
