"""
Enhanced GitHub Repository Extractor

Intelligently extracts GitHub repository information from user messages
in various formats with confidence scoring.
"""
import re
import logging
from typing import List, Dict, Any, Optional
from orchestration.shared.models import Reference, ReferenceType
from orchestration.message_parser.extractors.repository_registry import get_global_registry

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
        # Get repository registry for intelligent matching
        self.repo_registry = get_global_registry()
        
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
        
        logger.info(f"📝 Extracting GitHub references from: '{message[:100]}...'")
        
        # Check if message contains GitHub-related keywords
        has_github_context = any(
            keyword in message.lower() 
            for keyword in self.github_keywords
        )
        logger.info(f"   GitHub context detected: {has_github_context} (keywords: {[k for k in self.github_keywords if k in message.lower()]})")
        
        # Try each pattern in priority order
        for pattern_config in self.patterns:
            pattern_name = pattern_config['name']
            pattern = pattern_config['pattern']
            base_confidence = pattern_config['confidence']
            
            matches = list(pattern.finditer(message))
            if matches:
                logger.info(f"   Pattern '{pattern_name}' found {len(matches)} potential match(es)")
            
            for match in matches:
                try:
                    logger.debug(f"      Trying match: '{match.group(0)}'")
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
                                f"   ✓ Extracted GitHub repo: {ref.normalized_value} "
                                f"(confidence: {ref.confidence:.2f}, pattern: {pattern_name})"
                            )
                        else:
                            logger.debug(f"      ✗ Validation failed for: {ref.normalized_value}")
                    elif ref:
                        logger.debug(f"      ✗ Duplicate repo: {ref.normalized_value}")
                except Exception as e:
                    logger.warning(f"   ✗ Failed to parse GitHub reference: {e}")
                    continue
        
        # Try to detect bare repo names (repo without owner) if GitHub context exists
        if has_github_context and len(references) == 0:
            logger.info("   No owner/repo format found, trying to detect bare repo names...")
            bare_repo_refs = self._extract_bare_repo_names_with_registry(message)
            references.extend(bare_repo_refs)
        
        if references:
            logger.info(f"✅ Total GitHub references extracted: {len(references)}")
            for ref in references:
                logger.info(f"   - {ref.normalized_value} (confidence: {ref.confidence:.2f})")
        else:
            logger.warning(f"⚠️  No GitHub references found in message")
            logger.info(f"   💡 Tip: Use format 'owner/repo' or full URL 'https://github.com/owner/repo'")
        
        return references
    
    def _extract_bare_repo_names_with_registry(self, message: str) -> List[Reference]:
        """
        Extract bare repository names using registry for intelligent owner matching
        
        Args:
            message: User message
            
        Returns:
            List of repo references with matched owners
        """
        references = []
        
        # Pattern for repo-like names with GitHub keywords nearby
        bare_repo_pattern = re.compile(
            r'(?:repo(?:sitory)?|project|codebase)\s+([a-zA-Z0-9_-]{3,100})|'
            r'([a-zA-Z0-9_-]{3,100})\s+repo(?:sitory)?',
            re.IGNORECASE
        )
        
        for match in bare_repo_pattern.finditer(message):
            repo_name = match.group(1) or match.group(2)
            
            # Skip if it contains slash (already in owner/repo format)
            if '/' in repo_name:
                continue
            
            # Skip common words
            if repo_name.lower() in self.invalid_owners or repo_name.lower() in {
                'repo', 'repository', 'project', 'code', 'data', 'the', 'this', 'that'
            }:
                continue
            
            # Try to find in registry
            logger.info(f"   🔍 Looking up '{repo_name}' in repository registry...")
            match_info = self.repo_registry.find_repository(repo_name, threshold=0.6)
            
            if match_info:
                # Found a match in registry!
                ref = Reference(
                    type=ReferenceType.GITHUB_URL,
                    raw_text=match.group(0).strip(),
                    normalized_value=match_info['full_path'],
                    metadata={
                        'owner': match_info['owner'],
                        'repo': match_info['repo'],
                        'pattern_matched': 'bare_repo_with_registry',
                        'registry_match_type': match_info['match_type'],
                        'registry_confidence': match_info['confidence']
                    },
                    confidence=match_info['confidence']
                )
                
                references.append(ref)
                logger.info(
                    f"   ✅ Registry match: '{repo_name}' → {match_info['full_path']} "
                    f"(confidence: {match_info['confidence']:.2f}, type: {match_info['match_type']})"
                )
            else:
                # Not in registry - create UNKNOWN reference
                ref = Reference(
                    type=ReferenceType.GITHUB_URL,
                    raw_text=match.group(0).strip(),
                    normalized_value=f"UNKNOWN/{repo_name}",
                    metadata={
                        'owner': 'UNKNOWN',
                        'repo': repo_name,
                        'pattern_matched': 'bare_repo_name',
                        'needs_owner': True,
                        'warning': f'Repository "{repo_name}" not found in registry. Please specify as "owner/{repo_name}"'
                    },
                    confidence=0.3
                )
                
                references.append(ref)
                logger.warning(
                    f"   ⚠️  Bare repo name '{repo_name}' not in registry (missing owner)\n"
                    f"      Please provide full path like 'owner/{repo_name}' or register it in the repository registry"
                )
        
        return references
    
    def _extract_bare_repo_names(self, message: str) -> List[Reference]:
        """
        Extract bare repository names (without owner) when there's strong GitHub context
        These get low confidence and require manual owner specification
        
        Args:
            message: User message
            
        Returns:
            List of bare repo references (marked as ambiguous)
        """
        references = []
        
        # Pattern for repo-like names with GitHub keywords nearby
        # Matches: "am-market-data repo", "repo am-market-data", "repository my-app"
        bare_repo_pattern = re.compile(
            r'(?:repo(?:sitory)?|project|codebase)\s+([a-zA-Z0-9_-]{3,100})|'
            r'([a-zA-Z0-9_-]{3,100})\s+repo(?:sitory)?',
            re.IGNORECASE
        )
        
        for match in bare_repo_pattern.finditer(message):
            repo_name = match.group(1) or match.group(2)
            
            # Skip if it contains slash (already in owner/repo format)
            if '/' in repo_name:
                continue
            
            # Skip common words
            if repo_name.lower() in self.invalid_owners or repo_name.lower() in {
                'repo', 'repository', 'project', 'code', 'data', 'the', 'this', 'that'
            }:
                continue
            
            # Create a reference with UNKNOWN owner
            ref = Reference(
                type=ReferenceType.GITHUB_URL,
                raw_text=match.group(0).strip(),
                normalized_value=f"UNKNOWN/{repo_name}",
                metadata={
                    'owner': 'UNKNOWN',
                    'repo': repo_name,
                    'pattern_matched': 'bare_repo_name',
                    'needs_owner': True,
                    'warning': f'Repository name "{repo_name}" found but owner is unknown. Please specify as "owner/{repo_name}"'
                },
                confidence=0.5  # Low confidence - needs owner
            )
            
            references.append(ref)
            logger.warning(
                f"   ⚠️  Bare repo name detected: '{repo_name}' (missing owner)\n"
                f"      Please provide full path like 'owner/{repo_name}' or 'https://github.com/owner/{repo_name}'"
            )
        
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
