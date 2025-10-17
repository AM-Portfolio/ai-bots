from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from shared.clients import GrafanaClient, JiraClient, GitHubClient

logger = logging.getLogger(__name__)


class DataInjector:
    def __init__(self):
        self.grafana_client = GrafanaClient()
        self.jira_client = JiraClient()
        self.github_client = GitHubClient()
    
    async def inject_logs(
        self,
        time_range_hours: int = 24,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Injecting logs for the last {time_range_hours} hours")
        
        logs = []
        
        return logs
    
    async def inject_metrics(
        self,
        query: str,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        logger.info(f"Injecting metrics: {query}")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        metrics = await self.grafana_client.query_metrics(
            query=query,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        return metrics or {}
    
    async def inject_tickets(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        logger.info(f"Injecting tickets: {jql}")
        
        tickets = self.jira_client.search_issues(jql, max_results)
        
        return tickets
    
    async def inject_github_data(
        self,
        repository: str,
        issue_number: int
    ) -> Dict[str, Any]:
        logger.info(f"Injecting GitHub data for {repository}#{issue_number}")
        
        issue = self.github_client.get_issue(repository, issue_number)
        
        return issue or {}


async def inject_data(
    source_type: str,
    **kwargs
) -> Dict[str, Any]:
    injector = DataInjector()
    
    if source_type == "logs":
        data = await injector.inject_logs(
            time_range_hours=kwargs.get('time_range_hours', 24),
            filters=kwargs.get('filters', {})
        )
    elif source_type == "metrics":
        data = await injector.inject_metrics(
            query=kwargs.get('query', ''),
            time_range_hours=kwargs.get('time_range_hours', 24)
        )
    elif source_type == "tickets":
        data = await injector.inject_tickets(
            jql=kwargs.get('jql', ''),
            max_results=kwargs.get('max_results', 50)
        )
    elif source_type == "github":
        data = await injector.inject_github_data(
            repository=kwargs.get('repository', ''),
            issue_number=kwargs.get('issue_number', 0)
        )
    else:
        logger.error(f"Unknown source type: {source_type}")
        data = {}
    
    return {"source": source_type, "data": data}
