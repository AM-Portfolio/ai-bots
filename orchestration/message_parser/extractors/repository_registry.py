"""
Repository Registry - Known Repositories Injector

Maintains a registry of frequently used repositories and provides
intelligent matching for partial repo names.
"""
import logging
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class RepositoryRegistry:
    """
    Registry of known GitHub repositories with intelligent matching
    
    Features:
    - Stores known repos with owner/repo mapping
    - Fuzzy matching for partial repo names
    - Case-insensitive matching
    - Similarity scoring
    """
    
    def __init__(self):
        # Known repositories - can be loaded from config/database
        self._known_repos: Dict[str, str] = {
            # Format: 'repo-name': 'owner/repo-name'
            # These will be populated from user's IntegrationsHub or manual config
        }
        
        # Cache for quick lookups
        self._repo_name_to_full: Dict[str, str] = {}
        self._rebuild_cache()
        
    def register_repository(self, owner: str, repo: str):
        """
        Register a repository in the registry
        
        Args:
            owner: Repository owner
            repo: Repository name
        """
        full_path = f"{owner}/{repo}"
        self._known_repos[repo.lower()] = full_path
        self._rebuild_cache()
        logger.info(f"📋 Registered repository: {full_path}")
    
    def register_from_url(self, github_url: str):
        """
        Register repository from GitHub URL
        
        Args:
            github_url: Full GitHub URL
        """
        match = re.match(r'https?://github\.com/([^/]+)/([^/]+)', github_url)
        if match:
            owner, repo = match.groups()
            repo = repo.rstrip('.git')
            self.register_repository(owner, repo)
    
    def bulk_register(self, repos: List[Dict[str, str]]):
        """
        Register multiple repositories at once
        
        Args:
            repos: List of dicts with 'owner' and 'repo' keys
        """
        for repo_info in repos:
            self.register_repository(repo_info['owner'], repo_info['repo'])
    
    def _rebuild_cache(self):
        """Rebuild lookup cache"""
        self._repo_name_to_full = {
            repo_name.lower(): full_path
            for repo_name, full_path in self._known_repos.items()
        }
    
    def find_repository(
        self, 
        partial_name: str, 
        threshold: float = 0.6
    ) -> Optional[Dict[str, any]]:
        """
        Find repository by partial name using fuzzy matching
        
        Args:
            partial_name: Partial repository name
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            Dict with match info or None
        """
        partial_lower = partial_name.lower().strip()
        
        # Exact match
        if partial_lower in self._repo_name_to_full:
            full_path = self._repo_name_to_full[partial_lower]
            owner, repo = full_path.split('/')
            logger.info(f"✓ Exact match: '{partial_name}' → {full_path}")
            return {
                'owner': owner,
                'repo': repo,
                'full_path': full_path,
                'confidence': 1.0,
                'match_type': 'exact'
            }
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for repo_name, full_path in self._known_repos.items():
            # Calculate similarity
            similarity = self._calculate_similarity(partial_lower, repo_name.lower())
            
            # Also check if partial is in the repo name
            if partial_lower in repo_name.lower():
                similarity = max(similarity, 0.85)
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                owner, repo = full_path.split('/')
                best_match = {
                    'owner': owner,
                    'repo': repo,
                    'full_path': full_path,
                    'confidence': similarity,
                    'match_type': 'fuzzy'
                }
        
        if best_match:
            logger.info(
                f"✓ Fuzzy match: '{partial_name}' → {best_match['full_path']} "
                f"(confidence: {best_match['confidence']:.2f})"
            )
        else:
            logger.debug(f"✗ No match found for: '{partial_name}'")
        
        return best_match
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings
        
        Uses multiple strategies:
        - Sequence matching
        - Substring matching
        - Token matching (handles dashes, underscores)
        """
        # Basic sequence matching
        seq_score = SequenceMatcher(None, str1, str2).ratio()
        
        # Token-based matching (split on - and _)
        tokens1 = set(re.split(r'[-_]', str1))
        tokens2 = set(re.split(r'[-_]', str2))
        
        if tokens1 and tokens2:
            common_tokens = tokens1.intersection(tokens2)
            token_score = len(common_tokens) / max(len(tokens1), len(tokens2))
        else:
            token_score = 0.0
        
        # Substring bonus
        substring_score = 0.0
        if str1 in str2 or str2 in str1:
            substring_score = 0.3
        
        # Weighted combination
        final_score = (
            seq_score * 0.5 +
            token_score * 0.3 +
            substring_score * 0.2
        )
        
        return min(1.0, final_score)
    
    def get_all_repositories(self) -> List[str]:
        """Get all registered repositories"""
        return list(self._known_repos.values())
    
    def clear(self):
        """Clear all registered repositories"""
        self._known_repos.clear()
        self._rebuild_cache()
        logger.info("🗑️  Repository registry cleared")
    
    def load_from_config(self, config: Dict[str, any]):
        """
        Load repositories from configuration
        
        Args:
            config: Config dict with 'repositories' key
        """
        if 'repositories' in config:
            repos = config['repositories']
            if isinstance(repos, list):
                self.bulk_register(repos)
            elif isinstance(repos, dict):
                for repo_name, owner in repos.items():
                    self.register_repository(owner, repo_name)
    
    def suggest_owner(self, repo_name: str) -> Optional[str]:
        """
        Suggest owner for a repository name
        
        Args:
            repo_name: Repository name without owner
            
        Returns:
            Suggested owner or None
        """
        match = self.find_repository(repo_name)
        if match:
            return match['owner']
        return None
    
    def __len__(self) -> int:
        """Get number of registered repositories"""
        return len(self._known_repos)
    
    def __contains__(self, repo_name: str) -> bool:
        """Check if repository is registered"""
        return repo_name.lower() in self._repo_name_to_full


# Global registry instance
_global_registry = RepositoryRegistry()


def get_global_registry() -> RepositoryRegistry:
    """Get the global repository registry instance"""
    return _global_registry


def initialize_default_repositories():
    """Initialize registry with commonly referenced repositories"""
    registry = get_global_registry()
    
    # Add common repos that users might reference
    # These can be overridden by user configuration
    default_repos = [
        {'owner': 'AM-Portfolio', 'repo': 'am-portfolio'},
        {'owner': 'AM-Portfolio', 'repo': 'am-market-data'},
        # Add more as needed
    ]
    
    registry.bulk_register(default_repos)
    logger.info(f"✅ Initialized repository registry with {len(registry)} default repositories")


# Auto-initialize with defaults
initialize_default_repositories()
