"""
Shared data models for orchestration layer
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class ReferenceType(Enum):
    """Types of references that can be parsed from messages"""
    GITHUB_URL = "github_url"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    JIRA_TICKET = "jira_ticket"
    JIRA_URL = "jira_url"
    CONFLUENCE_URL = "confluence_url"
    GENERIC_URL = "generic_url"


class ContextSourceType(Enum):
    """Sources of enriched context data"""
    GITHUB_REPOSITORY = "github_repository"
    GITHUB_ISSUE = "github_issue"
    GITHUB_PR = "github_pr"
    GITHUB_FILE = "github_file"
    JIRA_ISSUE = "jira_issue"
    CONFLUENCE_PAGE = "confluence_page"
    GRAFANA_METRICS = "grafana_metrics"


@dataclass
class Reference:
    """A parsed reference from user message"""
    type: ReferenceType
    raw_text: str
    normalized_value: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ParsedMessage:
    """Result of message parsing"""
    original_message: str
    references: List[Reference] = field(default_factory=list)
    clean_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextData:
    """Enriched context from a single source"""
    source_type: ContextSourceType
    source_id: str
    data: Dict[str, Any]
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnrichedContext:
    """Complete enriched context for a message"""
    parsed_message: ParsedMessage
    context_items: List[ContextData] = field(default_factory=list)
    enriched_at: datetime = field(default_factory=datetime.utcnow)
    total_items: int = 0
    
    def __post_init__(self):
        self.total_items = len(self.context_items)


@dataclass
class PromptTemplate:
    """Template for LLM prompt generation"""
    template_name: str
    system_prompt: str
    user_prompt_template: str
    context_format: str
    variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormattedPrompt:
    """Final formatted prompt ready for LLM"""
    system_prompt: str
    user_prompt: str
    context_summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentTask:
    """Task for LangGraph agent to execute"""
    task_id: str
    task_type: str
    description: str
    context: EnrichedContext
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
