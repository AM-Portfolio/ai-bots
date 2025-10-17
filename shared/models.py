from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict, List
from enum import Enum


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True
    )


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, Enum):
    BUG = "bug"
    FEATURE = "feature"
    INCIDENT = "incident"
    TASK = "task"


class SourceType(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    GRAFANA = "grafana"
    CONFLUENCE = "confluence"
    TEAMS = "teams"


class Context(BaseModel):
    issue_id: str
    title: str
    description: str
    source: SourceType
    severity: SeverityLevel = SeverityLevel.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EnrichedContext(Context):
    code_snippets: List[str] = Field(default_factory=list)
    related_issues: List[str] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    stack_traces: List[str] = Field(default_factory=list)


class CodeFix(BaseModel):
    file_path: str
    original_code: str
    fixed_code: str
    explanation: str
    test_code: Optional[str] = None


class AnalysisResult(BaseModel):
    issue_id: str
    root_cause: str
    affected_components: List[str]
    suggested_fixes: List[CodeFix]
    confidence_score: float
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    test_id: str
    status: str
    passed: bool
    logs: str
    duration: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentationPage(BaseModel):
    page_id: Optional[str] = None
    title: str
    content: str
    parent_page_id: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
