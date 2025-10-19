"""
GitHub Repository Loader

Automatically loads user's GitHub repositories into the registry
using GitHub API with authentication token.
"""
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import requests
from orchestration.message_parser.extractors.repository_registry import get_global_registry

logger = logging.getLogger(__name__)

# Load environment variables if not already loaded
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded environment variables from {env_path}")
except Exception as e:
    logger.debug(f"Could not load .env file: {e}")


class GitHubRepoLoader:
    """
    Loads repositories from GitHub API and populates the registry
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub repo loader
        
        Args:
            token: GitHub personal access token (defaults to env var)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AI-Dev-Agent'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            logger.info("✅ GitHub API client initialized with authentication token")
        else:
            logger.warning("⚠️  No GitHub token found - API calls will be rate-limited")
    
    def load_user_repos(self, username: Optional[str] = None) -> int:
        """
        Load all repositories for a user
        
        Args:
            username: GitHub username (if None, loads authenticated user's repos)
            
        Returns:
            Number of repositories loaded
        """
        if username:
            url = f'{self.base_url}/users/{username}/repos'
            logger.info(f"📥 Fetching repositories for user: {username}")
        else:
            url = f'{self.base_url}/user/repos'
            logger.info(f"📥 Fetching repositories for authenticated user")
        
        try:
            repos = self._fetch_all_pages(url)
            count = self._register_repos(repos)
            logger.info(f"✅ Successfully loaded {count} repositories into registry")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to load repositories: {e}")
            return 0
    
    def load_org_repos(self, org_name: str) -> int:
        """
        Load all repositories for an organization
        
        Args:
            org_name: GitHub organization name
            
        Returns:
            Number of repositories loaded
        """
        url = f'{self.base_url}/orgs/{org_name}/repos'
        logger.info(f"📥 Fetching repositories for organization: {org_name}")
        
        try:
            repos = self._fetch_all_pages(url)
            count = self._register_repos(repos)
            logger.info(f"✅ Successfully loaded {count} organization repositories into registry")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to load organization repositories: {e}")
            return 0
    
    def load_specific_repo(self, owner: str, repo: str) -> bool:
        """
        Load a specific repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            True if successful
        """
        url = f'{self.base_url}/repos/{owner}/{repo}'
        logger.info(f"📥 Fetching repository: {owner}/{repo}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            repo_data = response.json()
            registry = get_global_registry()
            registry.register_repository(repo_data['owner']['login'], repo_data['name'])
            
            logger.info(f"✅ Successfully loaded repository: {owner}/{repo}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load repository {owner}/{repo}: {e}")
            return False
    
    def _fetch_all_pages(self, url: str, per_page: int = 100) -> List[Dict]:
        """
        Fetch all pages of results from GitHub API
        
        Args:
            url: API endpoint URL
            per_page: Results per page (max 100)
            
        Returns:
            List of repository data
        """
        all_repos = []
        page = 1
        
        while True:
            params = {'per_page': per_page, 'page': page}
            
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                repos = response.json()
                
                if not repos:
                    break
                
                all_repos.extend(repos)
                logger.debug(f"   Fetched page {page}: {len(repos)} repositories")
                
                # Check if there are more pages
                if len(repos) < per_page:
                    break
                
                page += 1
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching page {page}: {e}")
                break
        
        return all_repos
    
    def _register_repos(self, repos: List[Dict]) -> int:
        """
        Register repositories in the global registry
        
        Args:
            repos: List of repository data from GitHub API
            
        Returns:
            Number of repositories registered
        """
        registry = get_global_registry()
        count = 0
        
        for repo in repos:
            try:
                owner = repo['owner']['login']
                name = repo['name']
                registry.register_repository(owner, name)
                count += 1
                logger.debug(f"   Registered: {owner}/{name}")
            except KeyError as e:
                logger.warning(f"   Skipped invalid repo data: {e}")
                continue
        
        return count
    
    def auto_load_from_env(self) -> int:
        """
        Automatically load repositories from environment configuration
        
        Checks for:
        - GITHUB_ORG: Organization name to load repos from
        - GITHUB_USER: Username to load repos from
        - If authenticated, loads user's own repos
        
        Returns:
            Total number of repositories loaded
        """
        total_count = 0
        
        # Load organization repos
        org = os.environ.get('GITHUB_ORG')
        if org:
            logger.info(f"🏢 Loading repositories for organization: {org}")
            total_count += self.load_org_repos(org)
        
        # Load user repos
        user = os.environ.get('GITHUB_USER')
        if user:
            logger.info(f"👤 Loading repositories for user: {user}")
            total_count += self.load_user_repos(user)
        elif self.token and not org:
            # If token exists but no user/org specified, load authenticated user's repos
            logger.info(f"👤 Loading repositories for authenticated user")
            total_count += self.load_user_repos()
        
        if total_count > 0:
            logger.info(f"✅ Auto-load complete: {total_count} repositories in registry")
        else:
            logger.warning(f"⚠️  No repositories loaded. Set GITHUB_ORG or GITHUB_USER in .env")
        
        return total_count


def auto_load_github_repos():
    """
    Auto-load GitHub repositories on module import
    
    This function is called automatically to populate the registry
    with user's GitHub repositories.
    """
    try:
        loader = GitHubRepoLoader()
        count = loader.auto_load_from_env()
        
        if count > 0:
            registry = get_global_registry()
            logger.info(
                f"📚 Repository registry initialized with {len(registry)} repositories:\n"
                f"   {', '.join(registry.get_all_repositories()[:10])}"
                + (f"... and {len(registry) - 10} more" if len(registry) > 10 else "")
            )
    except Exception as e:
        logger.error(f"❌ Failed to auto-load GitHub repositories: {e}")


# Auto-load repositories when module is imported
auto_load_github_repos()
