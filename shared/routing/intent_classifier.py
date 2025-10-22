"""
Intent Classifier

Classifies user intent as repo-related or general conversation
"""

from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifies user intent as repo-related or general"""
    
    # Repo-related keywords
    REPO_KEYWORDS = [
        "code", "repo", "repository", "file", "function", "class", "method",
        "bug", "issue", "pull request", "pr", "commit", "branch", "merge",
        "test", "deploy", "build", "ci/cd", "pipeline", "github", "git",
        "analyze", "refactor", "optimize", "debug", "fix", "implement",
        "documentation", "readme", "api", "endpoint", "database", "db",
        "module", "package", "library", "dependency", "import", "export",
        "error", "exception", "trace", "stack", "log", "lint", "format"
    ]
    
    # Reference patterns (regex)
    REFERENCE_PATTERNS = [
        r'#\d+',  # Issue/PR numbers (#123)
        r'[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+',  # repo/name or org/repo
        r'[a-zA-Z0-9_-]+\.py',  # Python files
        r'[a-zA-Z0-9_-]+\.js',  # JavaScript files
        r'[a-zA-Z0-9_-]+\.ts',  # TypeScript files
        r'[a-zA-Z0-9_-]+\.java',  # Java files
        r'[a-zA-Z0-9_-]+\.go',  # Go files
        r'[a-zA-Z0-9_-]+\.rs',  # Rust files
        r'[a-zA-Z0-9_-]+\.[a-zA-Z]{2,4}',  # Other files
        r'src/[a-zA-Z0-9_/-]+',  # Source paths
        r'test/[a-zA-Z0-9_/-]+',  # Test paths
    ]
    
    # General conversation keywords (indicate non-repo queries)
    GENERAL_KEYWORDS = [
        "hello", "hi", "hey", "thanks", "thank you",
        "what is", "how to", "explain", "define",
        "weather", "news", "joke", "story", "chat",
        "how are you", "who are you", "what can you do"
    ]
    
    def __init__(self, repo_threshold: float = 0.3, general_threshold: float = 0.4):
        """
        Initialize intent classifier
        
        Args:
            repo_threshold: Confidence threshold for repo classification
            general_threshold: Confidence threshold for general classification
        """
        self.repo_threshold = repo_threshold
        self.general_threshold = general_threshold
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify user intent
        
        Args:
            text: User input text
            
        Returns:
            {
                "is_repo_related": bool,
                "confidence": float (0.0 to 1.0),
                "matched_keywords": list,
                "matched_patterns": list,
                "reason": str
            }
        """
        text_lower = text.lower()
        
        # Check for repo keywords
        matched_repo_keywords = [
            kw for kw in self.REPO_KEYWORDS
            if kw in text_lower
        ]
        
        # Check for general keywords
        matched_general_keywords = [
            kw for kw in self.GENERAL_KEYWORDS
            if kw in text_lower
        ]
        
        # Check for reference patterns
        matched_patterns = []
        for pattern in self.REFERENCE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                matched_patterns.extend(matches)
        
        # Calculate scores
        repo_keyword_score = min(len(matched_repo_keywords) * 0.15, 0.6)
        pattern_score = min(len(matched_patterns) * 0.3, 0.4)
        general_penalty = len(matched_general_keywords) * 0.2
        
        # Total confidence for repo-related
        repo_confidence = max(0.0, repo_keyword_score + pattern_score - general_penalty)
        
        # Determine classification
        is_repo_related = repo_confidence > self.repo_threshold
        
        # Generate reason
        if is_repo_related:
            reason = f"Detected {len(matched_repo_keywords)} repo keywords and {len(matched_patterns)} code references"
        elif matched_general_keywords:
            reason = f"Detected general conversation keywords: {', '.join(matched_general_keywords[:3])}"
        else:
            reason = "Low confidence for both repo and general categories"
        
        result = {
            "is_repo_related": is_repo_related,
            "confidence": repo_confidence,
            "matched_keywords": matched_repo_keywords,
            "matched_patterns": matched_patterns,
            "matched_general": matched_general_keywords,
            "reason": reason
        }
        
        logger.info(
            f"Intent: {'REPO-RELATED' if is_repo_related else 'GENERAL'} "
            f"(confidence: {repo_confidence:.2f})"
        )
        logger.debug(f"   • Repo keywords: {matched_repo_keywords}")
        logger.debug(f"   • Patterns: {matched_patterns}")
        logger.debug(f"   • General keywords: {matched_general_keywords}")
        
        return result
    
    def classify_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Classify multiple texts
        
        Args:
            texts: List of text inputs
            
        Returns:
            List of classification results
        """
        return [self.classify(text) for text in texts]
