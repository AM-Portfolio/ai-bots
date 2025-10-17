from typing import Optional
import logging
import time

from .dto import ContextResolverInput, ContextResolverOutput
from .domain import ContextEnricher
from .model import EnrichedContextModel
from shared.models import Context, SourceType
from shared.clients import GitHubClient, JiraClient, GrafanaClient

logger = logging.getLogger(__name__)


class ContextResolverService:
    def __init__(self):
        self.github_client = GitHubClient()
        self.jira_client = JiraClient()
        self.grafana_client = GrafanaClient()
        self.enricher = ContextEnricher()
    
    async def resolve(self, input_data: ContextResolverInput) -> ContextResolverOutput:
        start_time = time.time()
        sources_queried = []
        
        try:
            base_context = await self._fetch_base_context(
                input_data.issue_id,
                input_data.source,
                input_data.repository
            )
            
            if not base_context:
                return ContextResolverOutput(
                    issue_id=input_data.issue_id,
                    success=False,
                    error_message="Failed to fetch base context"
                )
            
            related_issues = []
            code_snippets = []
            logs = []
            metrics = {}
            
            if input_data.include_related_issues:
                related_issues = await self._fetch_related_issues(base_context)
                sources_queried.append("related_issues")
            
            code_snippets = await self._fetch_code_context(base_context, input_data.repository)
            sources_queried.append("code_context")
            
            if input_data.include_logs:
                logs = await self._fetch_logs(base_context, input_data.time_range_hours)
                sources_queried.append("logs")
            
            if input_data.include_metrics:
                metrics = await self._fetch_metrics(base_context)
                sources_queried.append("metrics")
            
            enriched = self.enricher.enrich_context(
                base_context,
                related_issues,
                code_snippets,
                logs,
                metrics
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return ContextResolverOutput(
                issue_id=input_data.issue_id,
                success=True,
                enriched_data=enriched.model_dump(),
                sources_queried=sources_queried,
                processing_time_ms=processing_time
            )
        
        except Exception as e:
            logger.error(f"Context resolution failed: {e}")
            return ContextResolverOutput(
                issue_id=input_data.issue_id,
                success=False,
                error_message=str(e),
                sources_queried=sources_queried
            )
    
    async def _fetch_base_context(
        self,
        issue_id: str,
        source: SourceType,
        repository: str
    ) -> Optional[Context]:
        if source == SourceType.GITHUB:
            issue_data = self.github_client.get_issue(repository, int(issue_id))
            if issue_data:
                return Context(
                    issue_id=str(issue_data['id']),
                    title=issue_data['title'],
                    description=issue_data['body'] or "",
                    source=SourceType.GITHUB,
                    metadata=issue_data
                )
        
        elif source == SourceType.JIRA:
            issue_data = self.jira_client.get_issue(issue_id)
            if issue_data:
                return Context(
                    issue_id=issue_data['key'],
                    title=issue_data['summary'],
                    description=issue_data['description'],
                    source=SourceType.JIRA,
                    metadata=issue_data
                )
        
        return None
    
    async def _fetch_related_issues(self, context: Context) -> list:
        related = []
        
        if context.source == SourceType.GITHUB and context.metadata.get('url'):
            try:
                repo_name = context.metadata.get('repository', {}).get('full_name')
                if repo_name:
                    search_query = f"is:issue repo:{repo_name} {context.title.split()[0]}"
                    issues = self.github_client.client.search_issues(search_query, order='desc')[:5]
                    for issue in issues:
                        if str(issue.number) != context.issue_id:
                            related.append({
                                'id': str(issue.number),
                                'title': issue.title,
                                'similarity': 0.7,
                                'source': 'github'
                            })
            except Exception as e:
                logger.warning(f"Failed to fetch related GitHub issues: {e}")
        
        elif context.source == SourceType.JIRA:
            try:
                jql = f'text ~ "{context.title.split()[0]}" AND key != {context.issue_id}'
                issues = self.jira_client.search_issues(jql, max_results=5)
                for issue in issues:
                    related.append({
                        'id': issue['key'],
                        'title': issue['summary'],
                        'similarity': 0.7,
                        'source': 'jira'
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch related Jira issues: {e}")
        
        return related
    
    async def _fetch_code_context(self, context: Context, repository: str) -> list:
        code_snippets = []
        
        if context.source == SourceType.GITHUB and repository:
            try:
                keywords = context.title.lower().split()
                for keyword in keywords[:3]:
                    try:
                        search_query = f"{keyword} in:file repo:{repository} language:python"
                        if self.github_client.client:
                            code_results = self.github_client.client.search_code(search_query, order='desc')
                            for item in list(code_results)[:3]:
                                content = self.github_client.get_file_content(repository, item.path)
                                if content:
                                    lines = content.split('\n')
                                    code_snippets.append({
                                        'file_path': item.path,
                                        'code': '\n'.join(lines[:50]),
                                        'line_start': 1,
                                        'line_end': min(50, len(lines)),
                                        'language': 'python'
                                    })
                                    break
                    except Exception as e:
                        logger.debug(f"Code search for '{keyword}' failed: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Failed to fetch code context: {e}")
        
        if not code_snippets and context.description:
            code_snippets.append({
                'file_path': 'context.txt',
                'code': context.description[:1000],
                'line_start': 1,
                'line_end': 50,
                'language': 'text'
            })
        
        return code_snippets
    
    async def _fetch_logs(self, context: Context, time_range_hours: int) -> list:
        logs = []
        
        if context.description:
            log_keywords = ['error', 'exception', 'failed', 'timeout', 'crash']
            description_lower = context.description.lower()
            
            if any(keyword in description_lower for keyword in log_keywords):
                logs.append({
                    'timestamp': context.created_at,
                    'level': 'ERROR',
                    'message': context.description[:500],
                    'source': 'issue_description',
                    'metadata': {}
                })
        
        return logs
    
    async def _fetch_metrics(self, context: Context) -> dict:
        metrics = {
            'error_rate': 0.0,
            'response_time': 0.0,
            'request_count': 0
        }
        
        if self.grafana_client.api_key:
            try:
                alerts = await self.grafana_client.get_alerts(state='alerting')
                if alerts:
                    metrics['active_alerts'] = len(alerts)
                    metrics['error_rate'] = 0.05
            except Exception as e:
                logger.warning(f"Failed to fetch metrics: {e}")
        
        severity_map = {
            'critical': 0.15,
            'high': 0.08,
            'medium': 0.03,
            'low': 0.01
        }
        metrics['error_rate'] = severity_map.get(context.severity.value, 0.02)
        
        return metrics


async def resolve_context(input_data: ContextResolverInput) -> ContextResolverOutput:
    service = ContextResolverService()
    return await service.resolve(input_data)
