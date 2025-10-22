"""
Repository State Manager for Incremental Embedding

Tracks embedded files using SHA256 hashing to enable:
- Incremental updates (only embed changed files)
- Caching of summaries and embeddings
- Fast failure recovery
- Deduplication
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FileState:
    """State information for a single file"""
    file_path: str
    sha256: str
    mtime: float
    size_bytes: int
    language: Optional[str] = None
    chunk_count: int = 0
    embedding_ids: List[str] = None
    summary_cached: bool = False
    last_embedded: Optional[str] = None  # ISO timestamp
    status: str = "pending"  # pending, processing, completed, failed
    
    def __post_init__(self):
        if self.embedding_ids is None:
            self.embedding_ids = []


@dataclass
class ChunkState:
    """State information for a code chunk"""
    chunk_id: str
    file_path: str
    chunk_hash: str
    chunk_index: int
    summary: Optional[str] = None
    embedding_id: Optional[str] = None
    created_at: Optional[str] = None
    status: str = "pending"


class RepoState:
    """
    Manages repository state for incremental embedding.
    
    Storage format: JSON manifest with file hashes and embedding metadata.
    Enables fast change detection and avoids re-processing unchanged code.
    """
    
    def __init__(self, manifest_path: str = ".code-intelligence-state.json"):
        """
        Initialize repo state manager.
        
        Args:
            manifest_path: Path to JSON manifest file
        """
        self.manifest_path = Path(manifest_path)
        self.file_states: Dict[str, FileState] = {}
        self.chunk_states: Dict[str, ChunkState] = {}
        self._load_manifest()
    
    def _load_manifest(self):
        """Load state from manifest file"""
        if not self.manifest_path.exists():
            logger.info(f"📋 No existing manifest found at {self.manifest_path}")
            return
        
        try:
            with open(self.manifest_path, 'r') as f:
                data = json.load(f)
            
            # Load file states
            for file_path, state_dict in data.get('files', {}).items():
                self.file_states[file_path] = FileState(**state_dict)
            
            # Load chunk states
            for chunk_id, state_dict in data.get('chunks', {}).items():
                self.chunk_states[chunk_id] = ChunkState(**state_dict)
            
            logger.info(
                f"✅ Loaded manifest: {len(self.file_states)} files, "
                f"{len(self.chunk_states)} chunks"
            )
        except Exception as e:
            logger.error(f"❌ Failed to load manifest: {e}")
            self.file_states = {}
            self.chunk_states = {}
    
    def save_manifest(self):
        """Save current state to manifest file"""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.utcnow().isoformat(),
                'files': {
                    path: asdict(state)
                    for path, state in self.file_states.items()
                },
                'chunks': {
                    chunk_id: asdict(state)
                    for chunk_id, state in self.chunk_states.items()
                },
                'stats': self.get_stats()
            }
            
            with open(self.manifest_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"💾 Saved manifest to {self.manifest_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save manifest: {e}")
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content"""
        sha256 = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {file_path}: {e}")
            return ""
    
    def compute_chunk_hash(self, content: str) -> str:
        """Compute hash of chunk content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_file_changed(self, file_path: str) -> bool:
        """
        Check if file has changed since last embedding.
        
        Returns:
            True if file is new or changed, False if unchanged
        """
        # New file
        if file_path not in self.file_states:
            return True
        
        # Check if file still exists
        if not os.path.exists(file_path):
            return True
        
        # Get current file info
        current_mtime = os.path.getmtime(file_path)
        current_hash = self.compute_file_hash(file_path)
        
        # Compare with stored state
        stored_state = self.file_states[file_path]
        
        # Hash changed = content changed
        if current_hash != stored_state.sha256:
            return True
        
        # Mtime changed but hash same = touch only, no change
        return False
    
    def get_changed_files(self, file_paths: List[str]) -> List[str]:
        """
        Get list of files that have changed.
        
        Args:
            file_paths: List of all files to check
            
        Returns:
            List of changed file paths
        """
        changed = []
        for file_path in file_paths:
            if self.is_file_changed(file_path):
                changed.append(file_path)
        
        logger.info(
            f"📊 Change detection: {len(changed)}/{len(file_paths)} files changed"
        )
        return changed
    
    def update_file_state(
        self,
        file_path: str,
        language: Optional[str] = None,
        chunk_count: int = 0,
        status: str = "completed"
    ):
        """Update state for a file"""
        file_hash = self.compute_file_hash(file_path)
        file_stat = os.stat(file_path)
        
        self.file_states[file_path] = FileState(
            file_path=file_path,
            sha256=file_hash,
            mtime=file_stat.st_mtime,
            size_bytes=file_stat.st_size,
            language=language,
            chunk_count=chunk_count,
            last_embedded=datetime.utcnow().isoformat(),
            status=status
        )
    
    def update_chunk_state(
        self,
        chunk_id: str,
        file_path: str,
        chunk_content: str,
        chunk_index: int,
        summary: Optional[str] = None,
        embedding_id: Optional[str] = None,
        status: str = "completed"
    ):
        """Update state for a chunk"""
        chunk_hash = self.compute_chunk_hash(chunk_content)
        
        self.chunk_states[chunk_id] = ChunkState(
            chunk_id=chunk_id,
            file_path=file_path,
            chunk_hash=chunk_hash,
            chunk_index=chunk_index,
            summary=summary,
            embedding_id=embedding_id,
            created_at=datetime.utcnow().isoformat(),
            status=status
        )
    
    def get_cached_summary(self, chunk_id: str) -> Optional[str]:
        """Get cached summary for a chunk if available"""
        if chunk_id in self.chunk_states:
            return self.chunk_states[chunk_id].summary
        return None
    
    def get_failed_chunks(self) -> List[str]:
        """Get list of chunks that failed to embed"""
        return [
            chunk_id
            for chunk_id, state in self.chunk_states.items()
            if state.status == "failed"
        ]
    
    def mark_failed(self, chunk_id: str):
        """Mark a chunk as failed"""
        if chunk_id in self.chunk_states:
            self.chunk_states[chunk_id].status = "failed"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about current state"""
        total_files = len(self.file_states)
        completed_files = sum(
            1 for state in self.file_states.values()
            if state.status == "completed"
        )
        
        total_chunks = len(self.chunk_states)
        completed_chunks = sum(
            1 for state in self.chunk_states.values()
            if state.status == "completed"
        )
        failed_chunks = sum(
            1 for state in self.chunk_states.values()
            if state.status == "failed"
        )
        
        return {
            'total_files': total_files,
            'completed_files': completed_files,
            'total_chunks': total_chunks,
            'completed_chunks': completed_chunks,
            'failed_chunks': failed_chunks,
            'cache_hit_rate': (
                completed_chunks / total_chunks * 100
                if total_chunks > 0 else 0
            )
        }
    
    def cleanup_deleted_files(self, current_files: Set[str]):
        """Remove state for files that no longer exist"""
        deleted = []
        for file_path in list(self.file_states.keys()):
            if file_path not in current_files:
                deleted.append(file_path)
                del self.file_states[file_path]
                
                # Also remove associated chunks
                chunks_to_remove = [
                    chunk_id
                    for chunk_id, state in self.chunk_states.items()
                    if state.file_path == file_path
                ]
                for chunk_id in chunks_to_remove:
                    del self.chunk_states[chunk_id]
        
        if deleted:
            logger.info(f"🧹 Cleaned up {len(deleted)} deleted files from manifest")
        
        return deleted
