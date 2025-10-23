from github import Github, GithubException
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self):
        self.client: Optional[Github] = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not settings.github_token:
            logger.warning("GitHub token not configured")
            return
        
        try:
            self.client = Github(settings.github_token)
            logger.info("GitHub client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            self.client = None
    
    async def get_issue(self, repo_name: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific issue from repository"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
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
        """Get a specific pull request from repository"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
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
        """Create a pull request"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(title=title, body=body, head=head, base=base)
            logger.info(f"Created PR #{pr.number} in {repo_name}")
            return pr.html_url
        except GithubException as e:
            logger.error(f"Failed to create PR in {repo_name}: {e}")
            return None

    async def get_file_content(self, repo_name: str, file_path: str, branch: str = "main") -> Optional[str]:
        """Get file content from repository"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            
            # Try to get file with specified branch, fallback to default branch
            try:
                file = repo.get_contents(file_path, ref=branch)
            except GithubException as e:
                if e.status == 404 and "No commit found" in str(e):
                    # Branch doesn't exist, try default branch
                    default_branch = repo.default_branch
                    logger.info(f"Branch '{branch}' not found, using default branch '{default_branch}'")
                    file = repo.get_contents(file_path, ref=default_branch)
                else:
                    raise
            
            if file.type == "file":
                return file.decoded_content.decode('utf-8')
            else:
                logger.error(f"Path {file_path} is not a file")
                return None
                
        except GithubException as e:
            logger.error(f"Failed to get file {file_path} from {repo_name}: {e}")
            return None

    async def create_or_update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main"
    ) -> bool:
        """Create or update a file in repository"""
        if not self.client:
            return False
        
        try:
            repo = self.client.get_repo(repo_name)
            
            try:
                # Try to get existing file
                existing_file = repo.get_contents(file_path, ref=branch)
                repo.update_file(
                    file_path,
                    commit_message,
                    content,
                    existing_file.sha,
                    branch=branch
                )
                logger.info(f"Updated file {file_path} in {repo_name}")
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(file_path, commit_message, content, branch=branch)
                logger.info(f"Created file {file_path} in {repo_name}")
            
            return True
        except GithubException as e:
            logger.error(f"Failed to create/update file {file_path} in {repo_name}: {e}")
            return False
    
    async def search_code(
        self,
        repo_name: str,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for code in a GitHub repository
        
        Args:
            repo_name: Repository name in format 'owner/repo'
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with path, content snippet, and score
        """
        if not self.client:
            logger.warning("GitHub client not initialized")
            return []
        
        try:
            # Build search query with repository scope
            search_query = f"{query} repo:{repo_name}"
            
            # Search code using GitHub API
            results = self.client.search_code(search_query)
            
            # Convert results to list of dicts
            code_results = []
            for idx, item in enumerate(results):
                if idx >= max_results:
                    break
                
                code_results.append({
                    'path': item.path,
                    'name': item.name,
                    'repository': item.repository.full_name,
                    'html_url': item.html_url,
                    'score': item.score,
                    'sha': item.sha
                })
            
            logger.info(f"🔍 Found {len(code_results)} code results for query: {query} in {repo_name}")
            return code_results
            
        except GithubException as e:
            logger.error(f"Failed to search code in {repo_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching code: {e}")
            return []
    
    async def get_multiple_files(
        self,
        repo_name: str,
        file_paths: List[str],
        ref: str = "main"
    ) -> Dict[str, str]:
        """
        Fetch contents of multiple files from a repository
        
        Args:
            repo_name: Repository name in format 'owner/repo'
            file_paths: List of file paths to fetch
            ref: Branch/tag/commit reference (default: "main")
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        if not self.client:
            logger.warning("GitHub client not initialized")
            return {}
        
        file_contents = {}
        
        for file_path in file_paths:
            try:
                content = self.get_file_content(repo_name, file_path, ref)
                if content:
                    file_contents[file_path] = content
                    logger.debug(f"✅ Fetched {file_path}")
                else:
                    logger.warning(f"⚠️  Could not fetch {file_path}")
            except Exception as e:
                logger.error(f"❌ Error fetching {file_path}: {e}")
                continue
        
        logger.info(f"📦 Fetched {len(file_contents)}/{len(file_paths)} files from {repo_name}")
        return file_contents

    async def get_multiple_files(self, repo_name: str, file_paths: List[str], branch: str = "main") -> Dict[str, Optional[str]]:
        """Get multiple files from repository"""
        results = {}
        
        if not self.client:
            return {path: None for path in file_paths}
        
        try:
            repo = self.client.get_repo(repo_name)
            
            for file_path in file_paths:
                try:
                    file_content = repo.get_contents(file_path, ref=branch)
                    if file_content.type == "file":
                        results[file_path] = file_content.decoded_content.decode('utf-8')
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

    async def search_code(self, query: str, repo_name: Optional[str] = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for code in repositories"""
        if not self.client:
            return []
        
        try:
            if repo_name:
                # Search within a specific repository
                search_query = f"{query} repo:{repo_name}"
            else:
                search_query = query
            
            results = self.client.search_code(search_query)
            
            search_results = []
            for result in results[:max_results]:  # Limit results based on parameter
                search_results.append({
                    "name": result.name,
                    "path": result.path,
                    "repository": result.repository.full_name,
                    "html_url": result.html_url,
                    "git_url": result.git_url,
                    "download_url": result.download_url,
                    "score": result.score
                })
            
            logger.info(f"Found {len(search_results)} code search results for query: {query}")
            return search_results
            
        except GithubException as e:
            logger.error(f"Failed to search code with query '{query}': {e}")
            return []

    async def get_repository_tree(self, repo_name: str, ref: str = "main", recursive: bool = True) -> Optional[List[Dict[str, Any]]]:
        """Get repository file tree structure"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            
            # Try to get the specified branch, fallback to default branch
            try:
                tree = repo.get_git_tree(ref, recursive=recursive)
            except GithubException:
                # Fallback to default branch
                default_branch = repo.default_branch
                logger.info(f"Branch '{ref}' not found, using default branch '{default_branch}'")
                tree = repo.get_git_tree(default_branch, recursive=recursive)
            
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

    async def list_directory(self, repo_name: str, path: str = "", ref: str = "main") -> Optional[List[Dict[str, Any]]]:
        """List files and directories at a specific path"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            contents = repo.get_contents(path, ref=ref)
            
            # Handle both single file and directory contents
            if not isinstance(contents, list):
                contents = [contents]
            
            items = []
            for item in contents:
                items.append({
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size,
                    "sha": item.sha,
                    "download_url": item.download_url,
                    "html_url": item.html_url
                })
            
            logger.info(f"Listed {len(items)} items in {repo_name}/{path}")
            return items
        except GithubException as e:
            logger.error(f"Failed to list directory {repo_name}/{path}: {e}")
            return None

    async def get_issues(self, repo_name: str, state: str = "open", limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """List issues from repository"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
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

    async def create_branch(self, repo_name: str, branch_name: str, base_branch: str = "main") -> bool:
        """Create a new branch from base branch"""
        if not self.client:
            return False
        
        try:
            repo = self.client.get_repo(repo_name)
            
            # Get the base branch reference
            try:
                base_ref = repo.get_git_ref(f"heads/{base_branch}")
            except GithubException:
                # Fallback to default branch
                default_branch = repo.default_branch
                logger.info(f"Branch '{base_branch}' not found, using default branch '{default_branch}'")
                base_ref = repo.get_git_ref(f"heads/{default_branch}")
            
            # Create new branch
            repo.create_git_ref(f"refs/heads/{branch_name}", base_ref.object.sha)
            logger.info(f"Created branch '{branch_name}' in {repo_name}")
            return True
        except GithubException as e:
            logger.error(f"Failed to create branch '{branch_name}' in {repo_name}: {e}")
            return False

    async def commit_documentation(self, repo_name: str, doc_content: str, file_path: str = "docs/AI_GENERATED_DOCS.md", commit_message: str = "docs: Add AI-generated documentation", branch: str = "main") -> Optional[Dict[str, Any]]:
        """Commit generated documentation to repository"""
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            
            # Get the default branch if needed
            default_branch = repo.default_branch
            logger.info(f"Default branch: '{default_branch}'")
            
            # Use provided branch or default
            target_branch = branch if branch != "main" or repo.default_branch == "main" else default_branch
            
            # Create or update the file
            try:
                existing_file = repo.get_contents(file_path, ref=target_branch)
                repo.update_file(
                    file_path,
                    commit_message,
                    doc_content,
                    existing_file.sha,
                    branch=target_branch
                )
                action = "updated"
            except GithubException:
                repo.create_file(
                    file_path,
                    commit_message,
                    doc_content,
                    branch=target_branch
                )
                action = "created"
            
            # Get the commit URL and file URL
            commits = repo.get_commits(path=file_path, sha=target_branch)
            latest_commit = commits[0] if commits.totalCount > 0 else None
            
            # Build file URL
            file_url = f"https://github.com/{repo_name}/blob/{target_branch}/{file_path}"
            
            result = {
                "action": action,
                "file_path": file_path,
                "branch": target_branch,
                "commit_url": latest_commit.html_url if latest_commit else None,
                "commit_sha": latest_commit.sha if latest_commit else None,
                "file_url": file_url
            }
            
            logger.info(f"{action.capitalize()} documentation file '{file_path}' in branch '{target_branch}' of {repo_name}")
            return result
        except GithubException as e:
            logger.error(f"Failed to commit documentation to {repo_name}: {e}")
            return None