"""
Code parsing and chunking module
"""
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from parsers import parser_registry

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for a code chunk"""
    file_path: str
    language: str
    chunk_type: str
    symbol_name: str
    start_line: int
    end_line: int
    token_count: int


@dataclass
class CodeChunk:
    """A chunk of code with metadata"""
    chunk_id: str
    content: str
    metadata: ChunkMetadata


class CodeParser:
    """Parses code files and generates chunks"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def parse_files(self, file_paths: List[str]) -> List[CodeChunk]:
        """
        Parse files and generate chunks.
        
        Args:
            file_paths: List of file paths to parse
            
        Returns:
            List of CodeChunk objects
        """
        logger.info(f"\n📝 Parsing {len(file_paths)} files...")
        
        all_chunks = []
        failed_files = 0
        
        for file_path in file_paths:
            try:
                chunks = self._parse_file(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"❌ Failed to parse {file_path}: {e}")
                failed_files += 1
        
        logger.info(f"✅ Parsed {len(file_paths) - failed_files}/{len(file_paths)} files")
        logger.info(f"   Generated {len(all_chunks)} chunks")
        if failed_files > 0:
            logger.warning(f"   ⚠️  {failed_files} files failed to parse")
        
        return all_chunks
    
    def _parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse a single file into chunks"""
        # Detect language
        ext = Path(file_path).suffix.lower()
        language = self._detect_language(ext)
        
        # Get appropriate parser
        parser = parser_registry.get_parser(language)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Parse and create chunks
        parsed_symbols = parser.parse(content, str(file_path))
        
        chunks = []
        rel_path = str(Path(file_path).relative_to(self.repo_path))
        
        for idx, symbol in enumerate(parsed_symbols):
            chunk_id = f"{rel_path}:{symbol.get('name', f'chunk_{idx}')}"
            
            metadata = ChunkMetadata(
                file_path=rel_path,
                language=language,
                chunk_type=symbol.get('type', 'unknown'),
                symbol_name=symbol.get('name', ''),
                start_line=symbol.get('start_line', 0),
                end_line=symbol.get('end_line', 0),
                token_count=len(symbol.get('code', '').split())
            )
            
            chunk = CodeChunk(
                chunk_id=chunk_id,
                content=symbol.get('code', ''),
                metadata=metadata
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.java': 'java',
            '.kt': 'kotlin',
            '.kts': 'kotlin',
            '.dart': 'dart',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        return ext_map.get(extension, 'unknown')
