"""
Conversation Context Extractor
Extracts structured context from conversation history
"""

import re
import logging
from typing import List, Dict, Any, Optional
from .models import ConversationContext, ConversationMessage, ContextType

logger = logging.getLogger(__name__)


class ConversationContextExtractor:
    """Extracts context from conversation history"""
    
    # Repository patterns (matches GitHub repo references)
    REPO_PATTERNS = [
        r'(?:repo|repository)\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # "repo owner/name"
        r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # Direct "owner/repo"
        r'github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)',  # Full URL
    ]
    
    # File path patterns
    FILE_PATTERNS = [
        r'(?:file|path)\s+([a-zA-Z0-9_\-/\.]+\.[a-z]+)',  # "file main.py"
        r'([a-zA-Z0-9_\-/]+\.[a-z]{2,4})',  # Direct file path with extension
        r'`([a-zA-Z0-9_\-/\.]+)`',  # Code-quoted paths
    ]
    
    # Code entity patterns (functions, classes, methods)
    CODE_ENTITY_PATTERNS = [
        r'(?:function|class|method)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # "function myFunc"
        r'([A-Z][a-zA-Z0-9]*)\s+(?:class|object)',  # "MyClass class"
        r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Python function definition
        r'class\s+([A-Z][a-zA-Z0-9]*)',  # Class definition
    ]
    
    # Topic keywords
    TOPIC_KEYWORDS = {
        'authentication': ['auth', 'login', 'signup', 'session', 'token', 'jwt'],
        'api': ['api', 'endpoint', 'route', 'rest', 'graphql'],
        'database': ['database', 'db', 'sql', 'query', 'table', 'model'],
        'testing': ['test', 'unit test', 'integration', 'e2e', 'pytest'],
        'documentation': ['docs', 'documentation', 'readme', 'guide'],
        'deployment': ['deploy', 'production', 'cicd', 'pipeline'],
        'frontend': ['react', 'vue', 'angular', 'ui', 'component'],
        'backend': ['server', 'backend', 'fastapi', 'flask', 'django'],
        'error_handling': ['error', 'exception', 'try', 'catch', 'handling'],
    }
    
    @classmethod
    def extract_context(
        cls, 
        conversation_history: List[Dict[str, Any]], 
        current_query: Optional[str] = None
    ) -> ConversationContext:
        """
        Extract structured context from conversation history
        
        Args:
            conversation_history: List of messages (dicts with 'role' and 'content')
            current_query: Current user query (optional)
            
        Returns:
            ConversationContext with extracted information
        """
        logger.info(f"🔍 Extracting context from {len(conversation_history)} messages")
        
        context = ConversationContext(conversation_depth=len(conversation_history))
        
        # Process each message in chronological order
        for msg in conversation_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Extract repositories
            repos = cls._extract_repositories(content)
            for repo in repos:
                if repo not in context.repositories_mentioned:
                    context.repositories_mentioned.append(repo)
                    # Update current repository to most recent mention
                    context.current_repository = repo
                    logger.info(f"📂 Extracted repository: {repo}")
            
            # Extract file paths (only from user messages to avoid assistant hallucinations)
            if role == 'user':
                files = cls._extract_file_paths(content)
                for file in files:
                    if file not in context.files_mentioned:
                        context.files_mentioned.append(file)
                        logger.info(f"📄 Extracted file: {file}")
            
            # Extract code entities
            entities = cls._extract_code_entities(content)
            for entity in entities:
                if entity not in context.code_entities:
                    context.code_entities.append(entity)
                    logger.info(f"🔧 Extracted code entity: {entity}")
            
            # Extract topics
            topics = cls._extract_topics(content)
            for topic in topics:
                if topic not in context.topics:
                    context.topics.append(topic)
                    logger.info(f"📌 Extracted topic: {topic}")
        
        # Process current query if provided
        if current_query:
            cls._update_context_from_current_query(context, current_query)
        
        # Limit list sizes to prevent context bloat
        context.repositories_mentioned = context.repositories_mentioned[-5:]  # Keep last 5
        context.files_mentioned = context.files_mentioned[-10:]
        context.code_entities = context.code_entities[-10:]
        context.topics = context.topics[-5:]
        
        logger.info(f"✅ Context extraction complete: {context.get_context_summary()}")
        return context
    
    @classmethod
    def _extract_repositories(cls, text: str) -> List[str]:
        """Extract repository references from text"""
        repos = []
        for pattern in cls.REPO_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                repo = match.group(1)
                # Validate format (must be owner/repo)
                if '/' in repo and len(repo.split('/')) == 2:
                    repos.append(repo)
        return list(set(repos))  # Remove duplicates
    
    @classmethod
    def _extract_file_paths(cls, text: str) -> List[str]:
        """Extract file paths from text"""
        files = []
        for pattern in cls.FILE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                file = match.group(1)
                # Filter out common false positives
                if not any(fp in file.lower() for fp in ['http://', 'https://', '@', 'www.']):
                    files.append(file)
        return list(set(files))
    
    @classmethod
    def _extract_code_entities(cls, text: str) -> List[str]:
        """Extract code entities (functions, classes) from text"""
        entities = []
        for pattern in cls.CODE_ENTITY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = match.group(1)
                # Filter out common words
                if len(entity) > 2 and not entity.lower() in ['the', 'and', 'for', 'with']:
                    entities.append(entity)
        return list(set(entities))
    
    @classmethod
    def _extract_topics(cls, text: str) -> List[str]:
        """Extract topics based on keyword matching"""
        text_lower = text.lower()
        topics = []
        
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            # Check if any keyword matches
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    @classmethod
    def _update_context_from_current_query(cls, context: ConversationContext, query: str) -> None:
        """Update context based on current query (may override history)"""
        # Check if current query mentions a new repository
        current_repos = cls._extract_repositories(query)
        if current_repos:
            # New repo mentioned - update current repository
            context.current_repository = current_repos[0]
            if current_repos[0] not in context.repositories_mentioned:
                context.repositories_mentioned.append(current_repos[0])
            logger.info(f"🔄 Updated current repository from query: {context.current_repository}")
