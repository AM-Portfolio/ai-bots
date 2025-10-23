"""
GitHub-LLM Module

Intelligent querying system that combines vector DB and GitHub API
using LangGraph orchestration for clean, structured responses.

Refactored with organized configuration and unified LLM client.
"""

from .orchestrator_config import GitHubLLMConfig
from .code_intelligence_client import CodeIntelligenceClient
from .query_orchestrator import GitHubLLMOrchestrator
from .models import QueryRequest, QueryResponse, QueryType, SourceResult

__all__ = [
    'GitHubLLMConfig',
    'CodeIntelligenceClient',
    'GitHubLLMOrchestrator',
    'QueryRequest',
    'QueryResponse',
    'QueryType',
    'SourceResult'
]
