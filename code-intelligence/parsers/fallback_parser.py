"""
Fallback parser for unsupported languages.

Uses simple line-based chunking with semantic boundaries
(blank lines, indentation changes) when tree-sitter is unavailable.
"""

from typing import List
from pathlib import Path
import logging

from .base_parser import BaseParser, CodeChunk, ChunkMetadata

logger = logging.getLogger(__name__)


class FallbackParser(BaseParser):
    """
    Generic fallback parser for any text-based code.
    
    Chunks code by:
    1. Blank line boundaries
    2. Function/class signatures (heuristic detection)
    3. Comment blocks
    4. Target token count (200-400 tokens)
    """
    
    def get_language(self) -> str:
        return "generic"
    
    def get_file_extension(self) -> List[str]:
        # Fallback handles everything
        return ['.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.html', '.css']
    
    def parse(self, content: str, file_path: str) -> List[dict]:
        """Parse content and return list of symbol dictionaries"""
        chunks = self._chunk_by_lines(file_path, content)
        
        # Convert chunks to symbol format expected by code_parser
        symbols = []
        for chunk in chunks:
            symbols.append({
                'type': chunk.metadata.chunk_type,
                'name': f'chunk_{chunk.metadata.start_line}',
                'code': chunk.content,
                'start_line': chunk.metadata.start_line,
                'end_line': chunk.metadata.end_line
            })
        return symbols
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse file using line-based chunking"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return self._chunk_by_lines(file_path, content)
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _chunk_by_lines(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk content by lines with semantic boundaries"""
        lines = content.split('\n')
        chunks = []
        
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        start_line = 0
        
        for i, line in enumerate(lines):
            line_tokens = self.estimate_tokens(line)
            
            # Check if we should start a new chunk
            should_break = False
            
            # Break on target size reached + semantic boundary
            if current_tokens + line_tokens > self.target_chunk_tokens:
                # Look for good break points
                if (not line.strip() or  # Blank line
                    self._is_semantic_boundary(line) or  # Function/class start
                    current_tokens > self.target_chunk_tokens * 0.8):  # 80% of target
                    should_break = True
            
            # Force break at max size
            if current_tokens + line_tokens > self.max_chunk_tokens:
                should_break = True
            
            if should_break and current_chunk:
                # Create chunk
                chunk_content = '\n'.join(current_chunk)
                
                # Skip trivial chunks
                if not self.should_skip_chunk(chunk_content, "code_block"):
                    chunk_id = self.create_chunk_id(file_path, chunk_index)
                    
                    metadata = ChunkMetadata(
                        chunk_id=chunk_id,
                        file_path=file_path,
                        language=self._detect_language(file_path),
                        start_line=start_line,
                        end_line=i,
                        chunk_type="code_block",
                        token_count=current_tokens,
                        content=chunk_content
                    )
                    
                    chunks.append(CodeChunk(metadata=metadata, content=chunk_content))
                    chunk_index += 1
                else:
                    logger.debug(f"Skipped trivial fallback chunk at line {start_line}")
                current_chunk = [line]
                current_tokens = line_tokens
                chunk_index += 1
                start_line = i
            else:
                current_chunk.append(line)
                current_tokens += line_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            
            # Skip trivial chunks
            if not self.should_skip_chunk(chunk_content, "code_block"):
                chunk_id = self.create_chunk_id(file_path, chunk_index)
                
                metadata = ChunkMetadata(
                    chunk_id=chunk_id,
                    file_path=file_path,
                    language=self._detect_language(file_path),
                    start_line=start_line,
                    end_line=len(lines),
                    chunk_type="code_block",
                    token_count=current_tokens,
                    content=chunk_content
                )
                
                chunks.append(CodeChunk(metadata=metadata, content=chunk_content))
            else:
                logger.debug(f"Skipped trivial final chunk at line {start_line}")
        
        logger.debug(f"Fallback parser created {len(chunks)} chunks from {file_path}")
        return chunks
    
    def _is_semantic_boundary(self, line: str) -> bool:
        """Detect if line is a semantic boundary (function, class, etc.)"""
        stripped = line.strip()
        
        # Common patterns for function/class definitions
        patterns = [
            'def ',      # Python
            'class ',    # Python, Java, etc.
            'function ', # JavaScript
            'const ',    # JavaScript
            'let ',      # JavaScript
            'var ',      # JavaScript
            'public ',   # Java, C++
            'private ',  # Java, C++
            'protected ',# Java, C++
            'async ',    # JavaScript, Python
            'export ',   # JavaScript
            'import ',   # Many languages
            '/**',       # JSDoc
            '/*',        # Block comment
        ]
        
        return any(stripped.startswith(p) for p in patterns)
    
    def _detect_language(self, file_path: str) -> str:
        """Simple language detection from file extension"""
        ext = Path(file_path).suffix.lower()
        
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.kt': 'kotlin',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.dart': 'dart',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.md': 'markdown',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        return ext_map.get(ext, 'text')
