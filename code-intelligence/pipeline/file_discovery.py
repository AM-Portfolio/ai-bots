"""
File discovery module - handles finding and filtering code files
"""
import os
import logging
from pathlib import Path
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.py', '.java', '.kt', '.kts', '.dart', '.js', '.jsx', '.ts', '.tsx',
    '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp',
    '.go', '.rs', '.rb', '.php', '.cs', '.swift',
    '.scala', '.r', '.m', '.mm', '.sh', '.sql',
    '.yaml', '.yml', '.json', '.xml', '.md'
}

IGNORED_DIRS = {
    '__pycache__', 'node_modules', '.git', '.venv', 'venv', 'env',
    'build', 'dist', '.idea', '.vscode', 'target', 'out', 'bin',
    '.gradle', '.mvn', 'vendor', 'deps', '.qdrant', '.next', '.nuxt'
}


class FileDiscovery:
    """Discovers and filters code files in a repository"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def discover_files(
        self,
        extensions: Optional[Set[str]] = None,
        ignore_dirs: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Discover all code files in repository.
        
        Args:
            extensions: File extensions to include (default: SUPPORTED_EXTENSIONS)
            ignore_dirs: Directories to ignore (default: IGNORED_DIRS)
            
        Returns:
            List of absolute file paths
        """
        logger.info(f"\n🔍 Discovering files in {self.repo_path}")
        
        supported_extensions = extensions or SUPPORTED_EXTENSIONS
        ignored_dirs = ignore_dirs or IGNORED_DIRS
        
        files = []
        skipped_dirs = 0
        skipped_files = 0
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            skipped_dirs += len([d for d in os.listdir(root) 
                               if d in ignored_dirs and os.path.isdir(os.path.join(root, d))])
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                ext = Path(filename).suffix.lower()
                
                if ext in supported_extensions:
                    files.append(file_path)
                else:
                    skipped_files += 1
        
        logger.info(f"✅ Found {len(files)} code files")
        logger.info(f"   Skipped {skipped_dirs} directories, {skipped_files} files")
        logger.info(f"   Supported extensions: {', '.join(list(supported_extensions)[:10])}...")
        
        return files
    
    def filter_by_paths(
        self,
        all_files: List[str],
        filter_paths: Set[str]
    ) -> List[str]:
        """
        Filter files by matching paths.
        
        Args:
            all_files: All discovered files
            filter_paths: Set of paths to match (e.g., from GitHub LLM)
            
        Returns:
            Filtered list of files
        """
        if not filter_paths:
            return all_files
        
        filtered = []
        for file_path in all_files:
            rel_path = str(Path(file_path).relative_to(self.repo_path))
            if rel_path in filter_paths or any(fp in rel_path for fp in filter_paths):
                filtered.append(file_path)
        
        logger.info(f"🎯 Filtered to {len(filtered)}/{len(all_files)} files using provided filter")
        return filtered
    
    def apply_limit(self, files: List[str], max_files: Optional[int]) -> List[str]:
        """Apply max files limit"""
        if max_files and len(files) > max_files:
            logger.info(f"⚠️  Limiting to first {max_files} files")
            return files[:max_files]
        return files

