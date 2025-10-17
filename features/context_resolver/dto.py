from typing import List, Dict, Any
from shared.models import BaseModel, SourceType


class ContextResolverInput(BaseModel):
    issue_id: str
    source: SourceType
    repository: str = ""
    include_logs: bool = True
    include_metrics: bool = True
    include_related_issues: bool = True
    time_range_hours: int = 24


class ContextResolverOutput(BaseModel):
    issue_id: str
    success: bool
    enriched_data: Dict[str, Any] = {}
    error_message: str = ""
    sources_queried: List[str] = []
    processing_time_ms: int = 0
