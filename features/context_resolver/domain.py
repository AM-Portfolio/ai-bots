from typing import List, Dict, Any, Optional
import logging

from .model import EnrichedContextModel, RelatedIssue, CodeContext, LogEntry
from shared.models import Context, SourceType, SeverityLevel

logger = logging.getLogger(__name__)


class ContextEnricher:
    @staticmethod
    def enrich_context(
        base_context: Context,
        related_issues: List[Dict[str, Any]],
        code_snippets: List[Dict[str, Any]],
        logs: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ) -> EnrichedContextModel:
        enriched = EnrichedContextModel(
            issue_id=base_context.issue_id,
            title=base_context.title,
            description=base_context.description,
            source=base_context.source,
            severity=base_context.severity
        )
        
        enriched.related_issues = [
            RelatedIssue(
                id=issue.get('id', ''),
                title=issue.get('title', ''),
                similarity_score=issue.get('similarity', 0.0),
                source=SourceType(issue.get('source', 'github'))
            )
            for issue in related_issues
        ]
        
        enriched.code_contexts = [
            CodeContext(
                file_path=snippet.get('file_path', ''),
                code_snippet=snippet.get('code', ''),
                line_start=snippet.get('line_start', 0),
                line_end=snippet.get('line_end', 0),
                language=snippet.get('language', 'python')
            )
            for snippet in code_snippets
        ]
        
        enriched.logs = [
            LogEntry(
                timestamp=log.get('timestamp'),
                level=log.get('level', 'INFO'),
                message=log.get('message', ''),
                source=log.get('source', 'unknown'),
                metadata=log.get('metadata', {})
            )
            for log in logs
        ]
        
        enriched.metrics = metrics
        
        return enriched
    
    @staticmethod
    def calculate_severity(
        issue_data: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> SeverityLevel:
        priority = issue_data.get('priority', '').lower()
        error_rate = metrics.get('error_rate', 0)
        
        if priority in ['critical', 'blocker'] or error_rate > 0.1:
            return SeverityLevel.CRITICAL
        elif priority == 'high' or error_rate > 0.05:
            return SeverityLevel.HIGH
        elif priority == 'medium':
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW
