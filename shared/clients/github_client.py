from github import Github, GithubException
from typing import List, Dict, Any, Optional
import logging

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
    
    def get_issue(self, repo_name: str, issue_number: int) -> Optional[Dict[str, Any]]:
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
    
    def get_pull_request(self, repo_name: str, pr_number: int) -> Optional[Dict[str, Any]]:
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
    
    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        body: str,
        head: str,
        base: str = "main"
    ) -> Optional[str]:
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
    
    def get_file_content(
        self,
        repo_name: str,
        file_path: str,
        ref: str = "main"
    ) -> Optional[str]:
        if not self.client:
            return None
        
        try:
            repo = self.client.get_repo(repo_name)
            content = repo.get_contents(file_path, ref=ref)
            return content.decoded_content.decode('utf-8')
        except GithubException as e:
            logger.error(f"Failed to get file {file_path} from {repo_name}: {e}")
            return None
    
    def create_or_update_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        message: str,
        branch: str = "main"
    ) -> bool:
        if not self.client:
            return False
        
        try:
            repo = self.client.get_repo(repo_name)
            
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


github_client = GitHubClient()
