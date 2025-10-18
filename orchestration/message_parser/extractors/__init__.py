"""
Message Parser Extractors

Specialized extractors for different reference types
"""
from orchestration.message_parser.extractors.github_extractor import GitHubExtractor
from orchestration.message_parser.extractors.repository_registry import (
    RepositoryRegistry,
    get_global_registry,
    initialize_default_repositories
)
from orchestration.message_parser.extractors.github_repo_loader import (
    GitHubRepoLoader,
    auto_load_github_repos
)

__all__ = [
    'GitHubExtractor',
    'RepositoryRegistry',
    'get_global_registry',
    'initialize_default_repositories',
    'GitHubRepoLoader',
    'auto_load_github_repos'
]
