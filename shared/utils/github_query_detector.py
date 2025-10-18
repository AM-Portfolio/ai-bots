"""
GitHub Query Detector
Detects if a user query is related to GitHub repositories, code, or requires GitHub context
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class GitHubQueryDetector:
    """Detects GitHub-related queries and extracts context"""
    
    # GitHub-related keywords (phrases are safe, short words moved to WORD_BOUNDARY_KEYWORDS)
    GITHUB_KEYWORDS = {
        'high_confidence': [
            'github', 'repository', 'repo', 'commit', 'pull request',
            'branch', 'fork', 'clone', 'code review', 'issue', 'merge request'
        ],
        'medium_confidence': [
            # Single words moved to WORD_BOUNDARY_KEYWORDS to prevent false positives
            'implementation', 'module', 'package', 'library', 'framework', 'codebase'
        ],
        'low_confidence': [
            'how does', 'explain', 'show me', 'find', 'search', 'locate',
            'where is', 'what is', 'documentation', 'docs'
        ]
    }
    
    # Patterns that require word boundaries (to avoid false positives)
    WORD_BOUNDARY_KEYWORDS = {
        # High confidence with word boundaries
        'git': r'\bgit\b',  # Avoid matching "digital", "legitimate"
        'pr': r'\bpr\b',  # Avoid matching "approaches", "april"
        'version control': r'\bversion\s+control\b',
        
        # Medium confidence with word boundaries  
        'api': r'\bapi\b',  # Avoid matching "capital", "rapid"
        'code': r'\bcode\b',  # Avoid matching "decode", "encode"
        'function': r'\bfunction\b',  # Avoid matching "dysfunctional"
        'class': r'\bclass\b',  # Avoid matching "classical"
        'method': r'\bmethod\b',  # Avoid matching "methodical"
    }
    
    # Repository name patterns
    REPO_PATTERNS = [
        r'(?:repo|repository)\s+([a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)?)',
        r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # owner/repo format
        r'github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # Full GitHub URL
    ]
    
    @classmethod
    def is_github_related(cls, query: str) -> bool:
        """
        Determine if a query is GitHub-related using word boundary matching
        
        Args:
            query: User query text
            
        Returns:
            True if query is GitHub-related
        """
        query_lower = query.lower()
        
        # Check for word-boundary keywords first (prevents false positives)
        for keyword, pattern in cls.WORD_BOUNDARY_KEYWORDS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.info(f"🎯 GitHub query detected (word boundary): keyword '{keyword}'")
                return True
        
        # Check for high confidence keywords
        for keyword in cls.GITHUB_KEYWORDS['high_confidence']:
            if keyword in query_lower:
                logger.info(f"🎯 GitHub query detected (high confidence): keyword '{keyword}'")
                return True
        
        # Check for repository patterns
        for pattern in cls.REPO_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.info(f"🎯 GitHub query detected: repository pattern found")
                return True
        
        # Check for medium + low confidence combination
        has_medium = any(kw in query_lower for kw in cls.GITHUB_KEYWORDS['medium_confidence'])
        has_low = any(kw in query_lower for kw in cls.GITHUB_KEYWORDS['low_confidence'])
        
        if has_medium and has_low:
            logger.info(f"🎯 GitHub query detected (medium confidence): code-related question")
            return True
        
        logger.info(f"ℹ️  Not a GitHub query: '{query[:50]}...'")
        return False
    
    @classmethod
    def extract_context(cls, query: str) -> Dict[str, Any]:
        """
        Extract GitHub context from query using word boundary matching
        
        Args:
            query: User query text
            
        Returns:
            Dictionary with extracted context (query_type is QueryType enum value)
        """
        context = {
            'is_github_related': cls.is_github_related(query),
            'repository': None,
            'keywords': [],
            'query_type': 'semantic_search'  # Default QueryType enum value
        }
        
        # Extract repository reference
        for pattern in cls.REPO_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                context['repository'] = match.group(1)
                logger.info(f"📍 Extracted repository: {context['repository']}")
                break
        
        # Extract relevant keywords using word boundaries
        query_lower = query.lower()
        
        # Check word boundary keywords
        for keyword, pattern in cls.WORD_BOUNDARY_KEYWORDS.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                context['keywords'].append(keyword)
        
        # Check phrase keywords
        for category, keywords in cls.GITHUB_KEYWORDS.items():
            found_keywords = [kw for kw in keywords if kw in query_lower]
            context['keywords'].extend(found_keywords)
        
        # Determine query type (must match QueryType enum values: semantic_search, code_search, file_explanation)
        if context['repository']:
            # Repository-specific query
            if re.search(r'\bcode\b', query_lower, re.IGNORECASE):
                context['query_type'] = 'code_search'
            elif any(kw in query_lower for kw in ['file', 'explain', 'documentation', 'docs']):
                context['query_type'] = 'file_explanation'
            else:
                context['query_type'] = 'semantic_search'
        elif any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in [r'\bcode\b', r'\bfunction\b', r'\bclass\b', r'\bmethod\b', r'\bapi\b']):
            context['query_type'] = 'code_search'
        elif any(kw in query_lower for kw in ['file', 'explain', 'documentation', 'docs']):
            context['query_type'] = 'file_explanation'
        else:
            context['query_type'] = 'semantic_search'
        
        logger.info(f"📊 GitHub context: type={context['query_type']}, repo={context['repository']}, keywords={len(context['keywords'])}")
        return context


# Quick helper functions
def is_github_query(query: str) -> bool:
    """Check if query is GitHub-related"""
    return GitHubQueryDetector.is_github_related(query)


def get_github_context(query: str) -> Dict[str, Any]:
    """Get GitHub context from query"""
    return GitHubQueryDetector.extract_context(query)
