"""
Enhanced GitHub Repository Extractor

Intelligently extracts GitHub repository information from user messages
in various formats with confidence scoring.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from orchestration.shared.models import Reference, ReferenceType

logger = logging.getLogger(__name__)


class GitHubExtractor:
    """
    Enhanced GitHub repository extractor supporting multiple formats:
    - Full URLs: https://github.com/owner/repo
    - Short URLs: github.com/owner/repo
    - Owner/repo format: facebook/react
    - Natural language: "check the facebook/react repository"
    - With paths: github.com/owner/repo/issues/123
    """
    
    def __init__(self):
        # Pattern priority order (higher priority first)
        self.patterns = [
            # Full HTTPS/HTTP GitHub URLs with optional paths
            {
                'name': 'full_url',
                'pattern': re.compile(
                    r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)'
                    r'(?:/(?:issues|pull)/(\d+)|/blob/([^/\s]+)/([^\s]+)|/tree/([^/\s]+)(?:/([^\s]+))?|/?)?',
                    re.IGNORECASE
                ),
                'confidence': 1.0
            },
            # Short GitHub URLs (without protocol)
            {
                'name': 'short_url',
                'pattern': re.compile(
                    r'(?:^|[\s,])github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)'
                    r'(?:/(?:issues|pull)/(\d+)|/blob/([^/\s]+)/([^\s]+)|/tree/([^/\s]+)(?:/([^\s]+))?|/?)?',
                    re.IGNORECASE
                ),
                'confidence': 0.95
            },
            # Owner/repo format with context keywords
            {
                'name': 'owner_repo_with_context',
                'pattern': re.compile(
                    r'(?:repository|repo|project|codebase|github)\s+(?:of\s+)?([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)',
                    re.IGNORECASE
                ),
                'confidence': 0.9
            },
            # Standalone owner/repo format (must have valid chars)
            {
                'name': 'owner_repo_standalone',
                'pattern': re.compile(
                    r'(?:^|[\s,("\'])([a-zA-Z0-9_-]{2,39})/([a-zA-Z0-9_.-]{1,100})(?:[\s,)"\'.]|$)'
                ),
                'confidence': 0.75
            },
            # @owner/repo mention format
            {
                'name': 'mention_format',
                'pattern': re.compile(
                    r'@([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)'
                ),
                'confidence': 0.85
            }
        ]
        
        # Common GitHub-related keywords that boost confidence
        self.github_keywords = [
            'github', 'repository', 'repo', 'codebase', 'project',
            'fork', 'clone', 'commit', 'pull request', 'pr', 'issue',
            'star', 'watch', 'branch', 'merge'
        ]
        
        # Invalid owner names (reserved, too common, etc.)
        self.invalid_owners = {
            'the', 'and', 'for', 'with', 'this', 'that', 'from', 'into',
            'http', 'https', 'www', 'com', 'org', 'net', 'io'
        }
    
    def extract(self, message: str) -> List[Reference]:
        """
        Extract all GitHub repository references from message
        
        Args:
            message: User message text
            
        Returns:
            List of Reference objects for GitHub repositories
        """
        references = []
        seen_repos = set()
        
        logger.debug(f"Extracting GitHub references from message: {message[:100]}...")
        
        # Check if message contains GitHub-related keywords
        has_github_context = any(
            keyword in message.lower() 
            for keyword in self.github_keywords
        )
        
        # Try each pattern in priority order
        for pattern_config in self.patterns:
            pattern_name = pattern_config['name']
            pattern = pattern_config['pattern']
            base_confidence = pattern_config['confidence']
            
            for match in pattern.finditer(message):
                try:
                    ref = self._create_reference(
                        match, 
                        pattern_name, 
                        base_confidence,
                        has_github_context
                    )
                    
                    if ref and ref.normalized_value not in seen_repos:
                        # Validate the reference
                        if self._validate_reference(ref):
                            references.append(ref)
                            seen_repos.add(ref.normalized_value)
                            logger.info(
                                f"Extracted GitHub repo: {ref.normalized_value} "
                                f"(confidence: {ref.confidence:.2f}, pattern: {pattern_name})"
                            )
                except Exception as e:
                    logger.warning(f"Failed to parse GitHub reference: {e}")
                    continue
        
        logger.info(f"Total GitHub references extracted: {len(references)}")
        return references
    
    def _create_reference(
        self,
        match: re.Match,
        pattern_name: str,
        base_confidence: float,
        has_github_context: bool
    ) -> Optional[Reference]:
        """Create Reference object from regex match"""
        groups = match.groups()
        owner = groups[0] if len(groups) > 0 else None
        repo = groups[1] if len(groups) > 1 else None
        
        if not owner or not repo:
            return None
        
        # Clean up repo name (remove .git suffix if present)
        repo = repo.rstrip('.git')
        
        # Determine reference type and extract additional metadata
        metadata: Dict[str, Any] = {
            'owner': owner,
            'repo': repo,
            'pattern_matched': pattern_name
        }
        
        ref_type = ReferenceType.GITHUB_URL
        
        # Check for issue/PR numbers
        if len(groups) > 2 and groups[2]:
            issue_or_pr = groups[2]
            if 'issue' in match.group(0).lower():
                ref_type = ReferenceType.GITHUB_ISSUE
                metadata['issue_number'] = issue_or_pr
            elif 'pull' in match.group(0).lower():
                ref_type = ReferenceType.GITHUB_PR
                metadata['pr_number'] = issue_or_pr
        
        # Check for branch and file path
        if len(groups) > 3:
            if groups[3]:  # blob branch
                metadata['branch'] = groups[3]
                if len(groups) > 4 and groups[4]:
                    metadata['file_path'] = groups[4]
            elif len(groups) > 5 and groups[5]:  # tree branch
                metadata['branch'] = groups[5]
                if len(groups) > 6 and groups[6]:
                    metadata['path'] = groups[6]
        
        # Adjust confidence based on context
        confidence = base_confidence
        if has_github_context and base_confidence < 0.9:
            confidence = min(1.0, base_confidence + 0.1)
        
        # Lower confidence for standalone owner/repo without context
        if pattern_name == 'owner_repo_standalone' and not has_github_context:
            confidence = 0.6
        
        return Reference(
            type=ref_type,
            raw_text=match.group(0).strip(),
            normalized_value=f"{owner}/{repo}",
            metadata=metadata,
            confidence=confidence
        )
    
    def _validate_reference(self, ref: Reference) -> bool:
        """
        Validate that the reference looks like a real GitHub repository
        
        Args:
            ref: Reference to validate
            
        Returns:
            True if reference appears valid
        """
        metadata = ref.metadata
        owner = metadata.get('owner', '')
        repo = metadata.get('repo', '')
        
        # Check owner is not in invalid list
        if owner.lower() in self.invalid_owners:
            logger.debug(f"Rejected invalid owner: {owner}")
            return False
        
        # Owner must be reasonable length (2-39 chars per GitHub rules)
        if not (2 <= len(owner) <= 39):
            logger.debug(f"Rejected owner with invalid length: {owner}")
            return False
        
        # Repo must be reasonable length (1-100 chars per GitHub rules)
        if not (1 <= len(repo) <= 100):
            logger.debug(f"Rejected repo with invalid length: {repo}")
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', owner):
            logger.debug(f"Rejected owner with invalid characters: {owner}")
            return False
        
        if not re.match(r'^[a-zA-Z0-9_.-]+$', repo):
            logger.debug(f"Rejected repo with invalid characters: {repo}")
            return False
        
        # Repo should not be just numbers (likely false positive)
        if repo.isdigit():
            logger.debug(f"Rejected numeric-only repo: {repo}")
            return False
        
        # Additional validation for low-confidence matches
        if ref.confidence < 0.8:
            # For low confidence, require at least 3 chars in repo name
            if len(repo) < 3:
                logger.debug(f"Rejected short repo name for low confidence match: {repo}")
                return False
        
        return True
    
    def extract_repo_info(self, repo_reference: str) -> Optional[Dict[str, str]]:
        """
        Extract owner and repo from a repository reference string
        
        Args:
            repo_reference: String like "owner/repo" or GitHub URL
            
        Returns:
            Dict with 'owner' and 'repo' keys, or None if invalid
        """
        refs = self.extract(repo_reference)
        if refs:
            return {
                'owner': refs[0].metadata['owner'],
                'repo': refs[0].metadata['repo']
            }
        return None
