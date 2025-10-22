"""
JavaScript/TypeScript parser using tree-sitter.

Handles JS, TS, JSX, TSX files and extracts functions, classes, and exports.
"""

from typing import List, Optional
import logging

from .base_parser import BaseParser, CodeChunk, ChunkMetadata

logger = logging.getLogger(__name__)

try:
    import tree_sitter_javascript as tsjs
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning("tree-sitter-javascript not available, using fallback")


class JavaScriptParser(BaseParser):
    """JavaScript/TypeScript parser using tree-sitter"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if HAS_TREE_SITTER:
            try:
                self.parser = Parser()
                JS_LANGUAGE = Language(tsjs.language(), 'javascript')
                self.parser.language = JS_LANGUAGE
                self.language_obj = JS_LANGUAGE
            except Exception as e:
                logger.error(f"Failed to initialize tree-sitter JavaScript: {e}")
                self.parser = None
        else:
            self.parser = None
    
    def get_language(self) -> str:
        return "javascript"
    
    def get_file_extension(self) -> List[str]:
        return ['.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse JavaScript/TypeScript file"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            if not self.parser:
                return self._fallback_parse(file_path, source_code.decode('utf-8'))
            
            tree = self.parser.parse(source_code)
            root_node = tree.root_node
            
            chunks = []
            chunk_index = 0
            
            # Extract relevant nodes
            for node in self._traverse_tree(root_node):
                if node.type in [
                    'function_declaration',
                    'arrow_function',
                    'function_expression',
                    'class_declaration',
                    'method_definition',
                    'export_statement'
                ]:
                    chunk = self._extract_chunk(node, source_code, file_path, chunk_index)
                    if chunk:
                        chunks.append(chunk)
                        chunk_index += 1
            
            if not chunks:
                chunks = self._fallback_parse(file_path, source_code.decode('utf-8'))
            
            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _traverse_tree(self, node, depth=0, max_depth=3):
        """Traverse tree to find relevant nodes"""
        if depth > max_depth:
            return
        
        yield node
        
        for child in node.children:
            yield from self._traverse_tree(child, depth + 1, max_depth)
    
    def _extract_chunk(
        self,
        node,
        source_code: bytes,
        file_path: str,
        chunk_index: int
    ) -> Optional[CodeChunk]:
        """Extract function/class as chunk"""
        content = source_code[node.start_byte:node.end_byte].decode('utf-8')
        
        # Get symbol name
        symbol_name = self._get_symbol_name(node, source_code)
        
        token_count = self.estimate_tokens(content)
        
        # Skip if too small (likely a simple assignment)
        if token_count < 20:
            return None
        
        # Truncate if too large
        if token_count > self.max_chunk_tokens:
            lines = content.split('\n')
            content = '\n'.join(lines[:20]) + '\n// ... (truncated)'
            token_count = self.estimate_tokens(content)
        
        chunk_id = self.create_chunk_id(file_path, chunk_index)
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            file_path=file_path,
            language="javascript",
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            chunk_type=node.type.replace('_declaration', '').replace('_statement', ''),
            symbol_name=symbol_name,
            token_count=token_count,
            dependencies=self.extract_dependencies(content),
            content=content
        )
        
        return CodeChunk(metadata=metadata, content=content)
    
    def _get_symbol_name(self, node, source_code: bytes) -> Optional[str]:
        """Extract function/class name"""
        for child in node.children:
            if child.type == 'identifier':
                return source_code[child.start_byte:child.end_byte].decode('utf-8')
        return None
    
    def _fallback_parse(self, file_path: str, content: str) -> List[CodeChunk]:
        """Fallback parsing"""
        from .fallback_parser import FallbackParser
        fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
        return fallback.parse_file(file_path)
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract imports/requires"""
        dependencies = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('import ', 'require(', 'from ')):
                dependencies.append(line)
        return dependencies
