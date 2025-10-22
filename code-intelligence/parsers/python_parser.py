"""
Python parser using tree-sitter.

Extracts functions, classes, and methods with proper semantic boundaries.
"""

from typing import List, Optional
import logging

from .base_parser import BaseParser, CodeChunk, ChunkMetadata

logger = logging.getLogger(__name__)

try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning("tree-sitter-python not available, using fallback")


class PythonParser(BaseParser):
    """Python-specific parser using tree-sitter"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if HAS_TREE_SITTER:
            try:
                self.parser = Parser()
                PY_LANGUAGE = Language(tspython.language(), 'python')
                self.parser.language = PY_LANGUAGE
                self.language_obj = PY_LANGUAGE
            except Exception as e:
                logger.error(f"Failed to initialize tree-sitter Python: {e}")
                self.parser = None
        else:
            self.parser = None
    
    def get_language(self) -> str:
        return "python"
    
    def get_file_extension(self) -> List[str]:
        return ['.py', '.pyw']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse Python file and extract functions/classes"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            if not self.parser:
                # Fallback to simple parsing
                return self._fallback_parse(file_path, source_code.decode('utf-8'))
            
            tree = self.parser.parse(source_code)
            root_node = tree.root_node
            
            chunks = []
            chunk_index = 0
            
            # Extract top-level definitions
            for node in root_node.children:
                if node.type in ['function_definition', 'class_definition']:
                    chunk = self._extract_chunk(
                        node, source_code, file_path, chunk_index
                    )
                    if chunk:
                        chunks.append(chunk)
                        chunk_index += 1
            
            # If no chunks found, fall back to whole file
            if not chunks:
                chunks = self._fallback_parse(file_path, source_code.decode('utf-8'))
            
            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _extract_chunk(
        self,
        node,
        source_code: bytes,
        file_path: str,
        chunk_index: int
    ) -> Optional[CodeChunk]:
        """Extract a single function or class as a chunk"""
        start_byte = node.start_byte
        end_byte = node.end_byte
        content = source_code[start_byte:end_byte].decode('utf-8')
        
        # Get symbol name
        symbol_name = None
        for child in node.children:
            if child.type == 'identifier':
                symbol_name = source_code[child.start_byte:child.end_byte].decode('utf-8')
                break
        
        # Check token count
        token_count = self.estimate_tokens(content)
        
        # Split if too large
        if token_count > self.max_chunk_tokens:
            return self._split_large_definition(
                node, source_code, file_path, chunk_index, symbol_name
            )
        
        chunk_id = self.create_chunk_id(file_path, chunk_index)
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            file_path=file_path,
            language="python",
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            chunk_type=node.type.replace('_definition', ''),
            symbol_name=symbol_name,
            token_count=token_count,
            dependencies=self.extract_dependencies(content),
            content=content
        )
        
        return CodeChunk(metadata=metadata, content=content)
    
    def _split_large_definition(
        self,
        node,
        source_code: bytes,
        file_path: str,
        chunk_index: int,
        symbol_name: Optional[str]
    ) -> Optional[CodeChunk]:
        """Handle large functions/classes by extracting just the signature + docstring"""
        # For large definitions, just take the first part (signature + docstring)
        start_byte = node.start_byte
        
        # Find docstring end or first 20 lines
        lines = source_code[start_byte:node.end_byte].decode('utf-8').split('\n')
        take_lines = min(20, len(lines))
        content = '\n'.join(lines[:take_lines])
        
        if take_lines < len(lines):
            content += '\n# ... (truncated for size)'
        
        chunk_id = self.create_chunk_id(file_path, chunk_index)
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            file_path=file_path,
            language="python",
            start_line=node.start_point[0],
            end_line=node.start_point[0] + take_lines,
            chunk_type=f"{node.type.replace('_definition', '')}_signature",
            symbol_name=symbol_name,
            token_count=self.estimate_tokens(content),
            dependencies=self.extract_dependencies(content),
            content=content
        )
        
        return CodeChunk(metadata=metadata, content=content)
    
    def _fallback_parse(self, file_path: str, content: str) -> List[CodeChunk]:
        """Simple fallback when tree-sitter fails"""
        from .fallback_parser import FallbackParser
        fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
        return fallback.parse_file(file_path)
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract Python imports"""
        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('import ', 'from ')):
                dependencies.append(line)
        return dependencies
