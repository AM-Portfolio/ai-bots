from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import logging

logger = logging.getLogger(__name__)


class Metrics:
    def __init__(self):
        self.issues_analyzed = Counter(
            'ai_dev_agent_issues_analyzed_total',
            'Total number of issues analyzed',
            ['source', 'severity']
        )
        
        self.fixes_generated = Counter(
            'ai_dev_agent_fixes_generated_total',
            'Total number of fixes generated'
        )
        
        self.prs_created = Counter(
            'ai_dev_agent_prs_created_total',
            'Total number of PRs created',
            ['repository']
        )
        
        self.analysis_duration = Histogram(
            'ai_dev_agent_analysis_duration_seconds',
            'Time spent analyzing issues',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.llm_calls = Counter(
            'ai_dev_agent_llm_calls_total',
            'Total number of LLM API calls',
            ['operation']
        )
        
        self.active_analyses = Gauge(
            'ai_dev_agent_active_analyses',
            'Number of currently active analyses'
        )
        
        logger.info("Metrics initialized")
    
    def record_issue_analyzed(self, source: str, severity: str):
        self.issues_analyzed.labels(source=source, severity=severity).inc()
    
    def record_fix_generated(self):
        self.fixes_generated.inc()
    
    def record_pr_created(self, repository: str):
        self.prs_created.labels(repository=repository).inc()
    
    def record_llm_call(self, operation: str):
        self.llm_calls.labels(operation=operation).inc()
    
    def get_metrics(self) -> Response:
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )


metrics = Metrics()
