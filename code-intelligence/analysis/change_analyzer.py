"""
Repository change analyzer - handles git-based change detection and prioritization
"""
import logging
from pathlib import Path
from typing import Dict, Any, List

from utils.change_planner import ChangePlanner

logger = logging.getLogger(__name__)


class ChangeAnalyzer:
    """Analyzes repository changes and prioritizes files"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.planner = ChangePlanner(repo_path=str(repo_path))
    
    def analyze_changes(
        self,
        base_ref: str = "HEAD",
        file_extensions: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze repository changes and calculate priorities.
        
        Args:
            base_ref: Git reference to compare against
            file_extensions: List of file extensions to analyze (e.g., ['.py', '.js'])
            
        Returns:
            Analysis results with changed files and priorities
        """
        logger.info(f"🔍 Analyzing repository changes from {base_ref}...")
        
        # Get changed files
        changed_files = self.planner.get_changed_files(base_ref=base_ref)
        
        # Get all files
        if file_extensions is None:
            file_extensions = ['.py']  # Default to Python
        
        all_files = []
        for ext in file_extensions:
            all_files.extend(list(self.repo_path.rglob(f"*{ext}")))
        
        # Calculate priorities
        priorities = self.planner.prioritize_files(
            all_files=[str(f.relative_to(self.repo_path)) for f in all_files],
            changed_files=changed_files
        )
        
        return {
            "changed_files": len(changed_files),
            "total_files": len(all_files),
            "priorities": priorities,
            "changed_file_list": changed_files
        }
    
    def display_priorities(self, priorities: list, max_display: int = 20):
        """Display priority breakdown"""
        print("\n📊 File Priorities:")
        print("=" * 80)
        
        by_priority = {}
        for p in priorities[:max_display]:
            if p.priority not in by_priority:
                by_priority[p.priority] = []
            by_priority[p.priority].append(p)
        
        for priority in sorted(by_priority.keys()):
            files = by_priority[priority]
            print(f"\nPriority {priority} ({len(files)} files):")
            for f in files[:5]:  # Show top 5 per priority
                status = "🔴 Changed" if f.is_changed else "⚪ Unchanged"
                entry = "📍 Entry" if f.is_entry_point else ""
                print(f"  {status} {entry} {f.file_path}")
                print(f"    Reason: {f.reason}")
