"""Java parser with tree-sitter support"""

from typing import List, Optional
import logging
from .base_parser import BaseParser, CodeChunk, ChunkMetadata
from .fallback_parser import FallbackParser

logger = logging.getLogger(__name__)

try:
    import tree_sitter_java as tsjava
    from tree_sitter import Language, Parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False
    logger.warning("tree-sitter-java not available, using fallback")


class JavaParser(BaseParser):
    """Java parser using tree-sitter"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if HAS_TREE_SITTER:
            try:
                self.parser = Parser()
                JAVA_LANGUAGE = Language(tsjava.language(), 'java')
                self.parser.language = JAVA_LANGUAGE
                self.language_obj = JAVA_LANGUAGE
            except Exception as e:
                logger.error(f"Failed to initialize tree-sitter Java: {e}")
                self.parser = None
        else:
            self.parser = None
    
    def get_language(self) -> str:
        return "java"
    
    def get_file_extension(self) -> List[str]:
        return ['.java']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse Java file and extract classes/methods"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()
            
            if not self.parser:
                # Fallback to simple parsing
                fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
                return fallback.parse_file(file_path)
            
            tree = self.parser.parse(source_code)
            root_node = tree.root_node
            
            chunks = []
            chunk_index = 0
            
            # Extract class and method definitions
            for node in self._find_definitions(root_node):
                if node.type in ['class_declaration', 'interface_declaration', 'method_declaration']:
                    chunk = self._extract_chunk(node, source_code, file_path, chunk_index)
                    if chunk:
                        if not self.should_skip_chunk(chunk.content, chunk.metadata.chunk_type):
                            chunks.append(chunk)
                            chunk_index += 1
                        else:
                            logger.debug(f"Skipped trivial chunk: {chunk.metadata.symbol_name}")
            
            # If no chunks found, fall back
            if not chunks:
                fallback = FallbackParser(self.target_chunk_tokens, self.max_chunk_tokens)
                chunks = fallback.parse_file(file_path)
            
            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []
    
    def _find_definitions(self, node):
        """Recursively find all class/method definitions"""
        definitions = []
        
        if node.type in ['class_declaration', 'interface_declaration', 'method_declaration']:
            definitions.append(node)
        
        for child in node.children:
            definitions.extend(self._find_definitions(child))
        
        return definitions
    
    def _extract_chunk(self, node, source_code: bytes, file_path: str, chunk_index: int) -> Optional[CodeChunk]:
        """Extract a single class or method as a chunk"""
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
            lines = content.split('\n')
            take_lines = min(20, len(lines))
            content = '\n'.join(lines[:take_lines])
            if take_lines < len(lines):
                content += f"\n... ({len(lines) - take_lines} more lines)"
            token_count = self.estimate_tokens(content)
        
        chunk_id = self.create_chunk_id(file_path, chunk_index)
        chunk_type = 'class' if 'class' in node.type or 'interface' in node.type else 'method'
        
        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            file_path=file_path,
            language="java",
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            chunk_type=chunk_type,
            symbol_name=symbol_name,
            token_count=token_count,
            dependencies=self.extract_dependencies(content),
            content=content
        )
        
        return CodeChunk(metadata=metadata, content=content)
