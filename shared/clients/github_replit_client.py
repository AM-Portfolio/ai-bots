"""GitHub client using Replit's GitHub integration"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from github import Github, GithubException

logger = logging.getLogger(__name__)


async def get_github_access_token() -> Optional[str]:
    """Get GitHub access token from Replit connector"""
    try:
        import aiohttp
        
        hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
        x_replit_token = None
        
        if os.environ.get('REPL_IDENTITY'):
            x_replit_token = 'repl ' + os.environ.get('REPL_IDENTITY')
        elif os.environ.get('WEB_REPL_RENEWAL'):
            x_replit_token = 'depl ' + os.environ.get('WEB_REPL_RENEWAL')
        
        if not x_replit_token or not hostname:
            logger.warning("Replit connector not available")
            return None
        
        url = f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=github'
        headers = {
            'Accept': 'application/json',
            'X_REPLIT_TOKEN': x_replit_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to get GitHub token: {response.status}")
                    return None
                
                data = await response.json()
                items = data.get('items', [])
                
                if not items:
                    logger.warning("No GitHub connection found")
                    return None
                
                connection_settings = items[0]
                access_token = (
                    connection_settings.get('settings', {}).get('access_token') or
                    connection_settings.get('settings', {}).get('oauth', {}).get('credentials', {}).get('access_token')
                )
                
                if not access_token:
                    logger.error("GitHub access token not found in connection")
                    return None
                
                return access_token
                
    except Exception as e:
        logger.error(f"Error getting GitHub access token: {e}")
        return None


class GitHubReplitClient:
    """GitHub client that uses Replit's GitHub integration"""
    
    def __init__(self):
        self.client: Optional[Github] = None
        self._access_token: Optional[str] = None
    
    async def _get_client(self) -> Optional[Github]:
        """Get or create GitHub client with fresh access token"""
        try:
            access_token = await get_github_access_token()
            if not access_token:
                return None
            
            if access_token != self._access_token:
                self._access_token = access_token
                self.client = Github(access_token)
                logger.info("GitHub client initialized with Replit integration")
            
            return self.client
            
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            return None
    
    async def get_issue(self, repo_name: str, issue_number: int) -> Optional[Dict[str, Any]]:
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            issue = repo.get_issue(issue_number)
            
            return {
                "id": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": issue.html_url
            }
        except GithubException as e:
            logger.error(f"Failed to get issue {repo_name}#{issue_number}: {e}")
            return None
    
    async def get_pull_request(self, repo_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "id": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "merged": pr.merged,
                "files_changed": pr.changed_files,
                "commits": pr.commits,
                "url": pr.html_url
            }
        except GithubException as e:
            logger.error(f"Failed to get PR {repo_name}#{pr_number}: {e}")
            return None
    
    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[str]:
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            logger.info(f"Created PR #{pr.number} in {repo_name}")
            return pr.html_url
        except GithubException as e:
            logger.error(f"Failed to create PR in {repo_name}: {e}")
            return None
    
    async def get_file_content(
        self,
        repo_name: str,
        file_path: str,
        ref: str = "main"
    ) -> Optional[str]:
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except GithubException as e:
            logger.error(f"Failed to get file {file_path} from {repo_name}: {e}")
            return None
    
    async def create_or_update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> bool:
        client = await self._get_client()
        if not client:
            return False
        
        try:
            repo = client.get_repo(repo_name)
            
            try:
                existing_file = repo.get_contents(file_path, ref=branch)
                repo.update_file(
                    file_path,
                    message,
                    content,
                    existing_file.sha,
                    branch=branch
                )
                logger.info(f"Updated file {file_path} in {repo_name}")
            except GithubException:
                repo.create_file(file_path, message, content, branch=branch)
                logger.info(f"Created file {file_path} in {repo_name}")
            
            return True
        except GithubException as e:
            logger.error(f"Failed to create/update file {file_path} in {repo_name}: {e}")
            return False
    
    async def get_repository_tree(
        self,
        repo_name: str,
        ref: str = "main",
        recursive: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Get repository file tree structure"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            tree = repo.get_git_tree(ref, recursive=recursive)
            
            files = []
            for item in tree.tree:
                files.append({
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "sha": item.sha,
                    "url": item.url
                })
            
            logger.info(f"Fetched {len(files)} items from {repo_name} tree")
            return files
        except GithubException as e:
            logger.error(f"Failed to get repository tree for {repo_name}: {e}")
            return None
    
    async def list_directory(
        self,
        repo_name: str,
        path: str = "",
        ref: str = "main"
    ) -> Optional[List[Dict[str, Any]]]:
        """List files and directories at a specific path"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            contents = repo.get_contents(path, ref=ref)
            
            items = []
            if isinstance(contents, list):
                for content in contents:
                    items.append({
                        "name": content.name,
                        "path": content.path,
                        "type": content.type,
                        "size": content.size,
                        "sha": content.sha
                    })
            else:
                items.append({
                    "name": contents.name,
                    "path": contents.path,
                    "type": contents.type,
                    "size": contents.size,
                    "sha": contents.sha
                })
            
            logger.info(f"Listed {len(items)} items in {repo_name}/{path}")
            return items
        except GithubException as e:
            logger.error(f"Failed to list directory {path} in {repo_name}: {e}")
            return None
    
    async def get_multiple_files(
        self,
        repo_name: str,
        file_paths: List[str],
        ref: str = "main"
    ) -> Dict[str, Optional[str]]:
        """Fetch multiple files at once"""
        client = await self._get_client()
        if not client:
            return {}
        
        results = {}
        try:
            repo = client.get_repo(repo_name)
            
            for file_path in file_paths:
                try:
                    content = repo.get_contents(file_path, ref=ref)
                    if hasattr(content, 'decoded_content'):
                        results[file_path] = content.decoded_content.decode('utf-8')
                    else:
                        results[file_path] = None
                except GithubException as e:
                    logger.warning(f"Could not fetch {file_path}: {e}")
                    results[file_path] = None
            
            logger.info(f"Fetched {len(results)} files from {repo_name}")
            return results
        except Exception as e:
            logger.error(f"Failed to fetch multiple files from {repo_name}: {e}")
            return results
    
    async def search_code(
        self,
        repo_name: str,
        query: str,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Search for code in repository"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            search_query = f"{query} repo:{repo_name}"
            results = client.search_code(search_query)
            
            items = []
            for i, result in enumerate(results):
                if i >= max_results:
                    break
                items.append({
                    "name": result.name,
                    "path": result.path,
                    "sha": result.sha,
                    "url": result.html_url,
                    "repository": result.repository.full_name
                })
            
            logger.info(f"Found {len(items)} code results for '{query}' in {repo_name}")
            return items
        except GithubException as e:
            logger.error(f"Failed to search code in {repo_name}: {e}")
            return None
    
    async def get_issues(
        self,
        repo_name: str,
        state: str = "open",
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """List issues from repository"""
        client = await self._get_client()
        if not client:
            return None
        
        try:
            repo = client.get_repo(repo_name)
            issues = repo.get_issues(state=state)
            
            result = []
            for i, issue in enumerate(issues):
                if i >= limit:
                    break
                result.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "url": issue.html_url
                })
            
            logger.info(f"Fetched {len(result)} issues from {repo_name}")
            return result
        except GithubException as e:
            logger.error(f"Failed to get issues from {repo_name}: {e}")
            return None


github_replit_client = GitHubReplitClient()
