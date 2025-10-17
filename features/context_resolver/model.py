from typing import List, Dict, Any, Optional
from datetime import datetime
from shared.models import BaseModel, SourceType, SeverityLevel


class ContextRequest(BaseModel):
    issue_id: str
    source: SourceType
    repository: Optional[str] = None
    additional_filters: Dict[str, Any] = {}


class RelatedIssue(BaseModel):
    id: str
    title: str
    similarity_score: float
    source: SourceType


class CodeContext(BaseModel):
    file_path: str
    code_snippet: str
    line_start: int
    line_end: int
    language: str


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: Dict[str, Any] = {}


class EnrichedContextModel(BaseModel):
    issue_id: str
    title: str
    description: str
    source: SourceType
    severity: SeverityLevel
    related_issues: List[RelatedIssue] = []
    code_contexts: List[CodeContext] = []
    logs: List[LogEntry] = []
    metrics: Dict[str, Any] = {}
    stack_traces: List[str] = []
    enrichment_timestamp: datetime = datetime.utcnow()
