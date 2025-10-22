"""
Change Planner for Smart Prioritization

Analyzes repository changes and prioritizes files for embedding based on:
1. Changed files (git diff)
2. Entry points and core modules
3. High-centrality files (imported by many others)
4. Dependencies of changed files
"""

import os
from pathlib import Path
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
import logging

try:
    from git import Repo
    HAS_GIT = True
except ImportError:
    HAS_GIT = False

logger = logging.getLogger(__name__)


@dataclass
class FilePriority:
    """Priority information for a file"""
    file_path: str
    priority: int  # 0 = highest, 10 = lowest
    reason: str
    is_changed: bool = False
    is_entry_point: bool = False
    dependency_count: int = 0


class ChangePlanner:
    """
    Intelligently prioritizes files for embedding.
    
    Priority levels:
    0 - Changed entry points
    1 - Changed core files
    2 - Changed regular files
    3 - Unchanged entry points
    4 - Unchanged core files
    5+ - Other files by dependency count
    """
    
    def __init__(self, repo_path: str = "."):
        """
        Initialize change planner.
        
        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)
        self.git_repo = None
        
        if HAS_GIT:
            try:
                self.git_repo = Repo(repo_path)
            except Exception as e:
                logger.warning(f"Not a git repository: {e}")
    
    def get_changed_files(
        self,
        base_ref: str = "HEAD",
        compare_ref: Optional[str] = None
    ) -> Set[str]:
        """
        Get files changed in git.
        
        Args:
            base_ref: Base reference (default: HEAD)
            compare_ref: Compare reference (default: working directory)
            
        Returns:
            Set of changed file paths
        """
        if not self.git_repo:
            logger.warning("No git repo, assuming all files changed")
            return set()
        
        try:
            # Get changed files in working directory
            changed_files = set()
            
            # Untracked files
            for item in self.git_repo.untracked_files:
                changed_files.add(item)
            
            # Modified files
            for item in self.git_repo.index.diff(None):
                changed_files.add(item.a_path)
            
            # Staged files
            for item in self.git_repo.index.diff("HEAD"):
                changed_files.add(item.a_path)
            
            logger.info(f"Found {len(changed_files)} changed files in working directory")
            return changed_files
            
        except Exception as e:
            logger.error(f"Failed to get git changes: {e}")
            return set()
    
    def detect_entry_points(self, all_files: List[str]) -> Set[str]:
        """
        Detect entry point files.
        
        Common patterns:
        - main.py, app.py, index.js, server.js
        - __init__.py in root packages
        - setup.py, package.json
        """
        entry_points = set()
        
        entry_patterns = [
            'main.py', 'app.py', 'run.py',
            'index.js', 'index.ts', 'server.js', 'server.ts',
            'main.java', 'Main.java', 'Application.java',
            'main.cpp', 'main.c',
            'main.dart', 'lib/main.dart',
            'app.kt', 'Main.kt',
            '__main__.py'
        ]
        
        for file_path in all_files:
            file_name = Path(file_path).name
            
            # Check exact matches
            if file_name in entry_patterns:
                entry_points.add(file_path)
                continue
            
            # Check __init__.py at package roots
            if file_name == '__init__.py':
                depth = len(Path(file_path).parts)
                if depth <= 3:  # Near root
                    entry_points.add(file_path)
        
        logger.info(f"Detected {len(entry_points)} entry points")
        return entry_points
    
    def analyze_dependencies(self, all_files: List[str]) -> Dict[str, int]:
        """
        Analyze import dependencies (simple heuristic).
        
        Returns:
            Dict mapping file_path -> import_count (how many files import it)
        """
        dependency_count = {f: 0 for f in all_files}
        
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for imports of other files in the project
                for other_file in all_files:
                    if other_file == file_path:
                        continue
                    
                    # Simple heuristic: check if filename appears in imports
                    file_stem = Path(other_file).stem
                    if file_stem in content:
                        dependency_count[other_file] = dependency_count.get(other_file, 0) + 1
                        
            except Exception as e:
                logger.debug(f"Couldn't read {file_path}: {e}")
                continue
        
        # Log high-centrality files
        high_centrality = [
            (f, count) for f, count in dependency_count.items()
            if count > 5
        ]
        if high_centrality:
            logger.info(
                f"High-centrality files: {len(high_centrality)} "
                f"(top: {sorted(high_centrality, key=lambda x: -x[1])[:3]})"
            )
        
        return dependency_count
    
    def prioritize_files(
        self,
        all_files: List[str],
        changed_files: Optional[Set[str]] = None
    ) -> List[FilePriority]:
        """
        Prioritize files for embedding.
        
        Args:
            all_files: All files to consider
            changed_files: Set of changed files (optional, will auto-detect)
            
        Returns:
            List of FilePriority sorted by priority (0 = highest)
        """
        if changed_files is None:
            changed_files = self.get_changed_files()
        
        entry_points = self.detect_entry_points(all_files)
        dependency_counts = self.analyze_dependencies(all_files)
        
        priorities = []
        
        for file_path in all_files:
            is_changed = file_path in changed_files
            is_entry = file_path in entry_points
            dep_count = dependency_counts.get(file_path, 0)
            
            # Determine priority
            if is_changed and is_entry:
                priority = 0
                reason = "Changed entry point"
            elif is_changed and dep_count > 5:
                priority = 1
                reason = "Changed core file (high imports)"
            elif is_changed:
                priority = 2
                reason = "Changed file"
            elif is_entry:
                priority = 3
                reason = "Entry point"
            elif dep_count > 5:
                priority = 4
                reason = "Core file (high imports)"
            else:
                # Priority based on dependencies (less important = higher number)
                priority = 5 + max(0, 10 - dep_count)
                reason = f"Regular file ({dep_count} imports)"
            
            priorities.append(FilePriority(
                file_path=file_path,
                priority=priority,
                reason=reason,
                is_changed=is_changed,
                is_entry_point=is_entry,
                dependency_count=dep_count
            ))
        
        # Sort by priority
        priorities.sort(key=lambda x: (x.priority, -x.dependency_count, x.file_path))
        
        logger.info(
            f"Prioritized {len(priorities)} files: "
            f"{sum(1 for p in priorities if p.is_changed)} changed, "
            f"{sum(1 for p in priorities if p.is_entry_point)} entry points"
        )
        
        return priorities
    
    def get_top_priority_files(
        self,
        all_files: List[str],
        max_files: int = 100,
        changed_files: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Get top priority files to embed first.
        
        Args:
            all_files: All files to consider
            max_files: Maximum number of files to return
            changed_files: Set of changed files (optional)
            
        Returns:
            List of file paths in priority order
        """
        priorities = self.prioritize_files(all_files, changed_files)
        return [p.file_path for p in priorities[:max_files]]
