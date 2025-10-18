"""
Context Enricher Implementation

Fetches data from GitHub, Jira, Confluence based on parsed references
"""
from typing import Dict, List, Optional, Any
from orchestration.shared.interfaces import IContextEnricher
from orchestration.shared.models import (
    ParsedMessage,
    EnrichedContext,
    ContextData,
    ContextSourceType,
    ReferenceType
)
from shared.services.manager import ServiceManager


class ContextEnricher(IContextEnricher):
    """Enriches parsed messages with data from external services"""
    
    def __init__(self, service_manager: ServiceManager):
        """
        Initialize enricher with service manager
        
        Args:
            service_manager: Service manager for accessing integrations
        """
        self.service_manager = service_manager
        self.cache: Dict[str, ContextData] = {}
    
    async def enrich(
        self,
        parsed_message: ParsedMessage,
        options: Optional[Dict[str, Any]] = None
    ) -> EnrichedContext:
        """
        Enrich parsed message with data from external sources
        
        Args:
            parsed_message: Parsed message with references
            options: Optional enrichment options
            
        Returns:
            EnrichedContext with fetched data
        """
        options = options or {}
        use_cache = options.get('use_cache', True)
        max_depth = options.get('max_depth', 2)
        
        context_items: List[ContextData] = []
        
        for ref in parsed_message.references:
            if ref.type in [ReferenceType.GITHUB_URL, ReferenceType.GITHUB_ISSUE, ReferenceType.GITHUB_PR]:
                items = await self._enrich_github_reference(ref, use_cache)
                context_items.extend(items)
            
            elif ref.type in [ReferenceType.JIRA_URL, ReferenceType.JIRA_TICKET]:
                items = await self._enrich_jira_reference(ref, use_cache)
                context_items.extend(items)
            
            elif ref.type == ReferenceType.CONFLUENCE_URL:
                items = await self._enrich_confluence_reference(ref, use_cache)
                context_items.extend(items)
        
        return EnrichedContext(
            parsed_message=parsed_message,
            context_items=context_items
        )
    
    async def _enrich_github_reference(
        self,
        reference: 'Reference',
        use_cache: bool
    ) -> List[ContextData]:
        """Enrich GitHub reference with repository/issue/PR data"""
        context_items = []
        cache_key = f"github_{reference.normalized_value}"
        
        if use_cache and cache_key in self.cache:
            return [self.cache[cache_key]]
        
        try:
            github_service = self.service_manager.get_service('github')
            
            owner = reference.metadata.get('owner')
            repo = reference.metadata.get('repo')
            
            if owner and repo:
                repo_info = await github_service.execute(
                    'get_repository',
                    owner=owner,
                    repo=repo
                )
                
                context_data = ContextData(
                    source_type=ContextSourceType.GITHUB_REPOSITORY,
                    source_id=f"{owner}/{repo}",
                    data={
                        'name': repo_info.get('name'),
                        'description': repo_info.get('description'),
                        'language': repo_info.get('language'),
                        'stars': repo_info.get('stargazers_count'),
                        'default_branch': repo_info.get('default_branch'),
                        'url': repo_info.get('html_url')
                    },
                    metadata=reference.metadata
                )
                
                context_items.append(context_data)
                if use_cache:
                    self.cache[cache_key] = context_data
            
            if reference.metadata.get('issue_number'):
                issue_num = reference.metadata['issue_number']
                issue_info = await github_service.execute(
                    'get_issue',
                    owner=owner,
                    repo=repo,
                    issue_number=int(issue_num)
                )
                
                context_data = ContextData(
                    source_type=ContextSourceType.GITHUB_ISSUE,
                    source_id=f"{owner}/{repo}#{issue_num}",
                    data={
                        'title': issue_info.get('title'),
                        'body': issue_info.get('body'),
                        'state': issue_info.get('state'),
                        'labels': [l.get('name') for l in issue_info.get('labels', [])],
                        'comments_count': issue_info.get('comments'),
                        'url': issue_info.get('html_url')
                    },
                    metadata=reference.metadata
                )
                
                context_items.append(context_data)
        
        except Exception as e:
            print(f"Error enriching GitHub reference: {e}")
        
        return context_items
    
    async def _enrich_jira_reference(
        self,
        reference: 'Reference',
        use_cache: bool
    ) -> List[ContextData]:
        """Enrich Jira reference with ticket data"""
        context_items = []
        cache_key = f"jira_{reference.normalized_value}"
        
        if use_cache and cache_key in self.cache:
            return [self.cache[cache_key]]
        
        try:
            jira_service = self.service_manager.get_service('jira')
            ticket_id = reference.metadata.get('ticket_id')
            
            if ticket_id:
                issue_info = await jira_service.execute(
                    'get_issue',
                    issue_key=ticket_id
                )
                
                fields = issue_info.get('fields', {})
                context_data = ContextData(
                    source_type=ContextSourceType.JIRA_ISSUE,
                    source_id=ticket_id,
                    data={
                        'key': issue_info.get('key'),
                        'summary': fields.get('summary'),
                        'description': fields.get('description'),
                        'status': fields.get('status', {}).get('name'),
                        'priority': fields.get('priority', {}).get('name'),
                        'issue_type': fields.get('issuetype', {}).get('name'),
                        'assignee': fields.get('assignee', {}).get('displayName'),
                        'created': fields.get('created')
                    },
                    metadata=reference.metadata
                )
                
                context_items.append(context_data)
                if use_cache:
                    self.cache[cache_key] = context_data
        
        except Exception as e:
            print(f"Error enriching Jira reference: {e}")
        
        return context_items
    
    async def _enrich_confluence_reference(
        self,
        reference: 'Reference',
        use_cache: bool
    ) -> List[ContextData]:
        """Enrich Confluence reference with page data"""
        context_items = []
        cache_key = f"confluence_{reference.normalized_value}"
        
        if use_cache and cache_key in self.cache:
            return [self.cache[cache_key]]
        
        try:
            confluence_service = self.service_manager.get_service('confluence')
            page_id = reference.metadata.get('page_id')
            
            if page_id:
                page_info = await confluence_service.execute(
                    'get_page',
                    page_id=page_id
                )
                
                context_data = ContextData(
                    source_type=ContextSourceType.CONFLUENCE_PAGE,
                    source_id=page_id,
                    data={
                        'id': page_info.get('id'),
                        'title': page_info.get('title'),
                        'content': page_info.get('body', {}).get('storage', {}).get('value'),
                        'space': page_info.get('space', {}).get('name'),
                        'url': page_info.get('_links', {}).get('webui')
                    },
                    metadata=reference.metadata
                )
                
                context_items.append(context_data)
                if use_cache:
                    self.cache[cache_key] = context_data
        
        except Exception as e:
            print(f"Error enriching Confluence reference: {e}")
        
        return context_items
    
    def clear_cache(self):
        """Clear the context cache"""
        self.cache.clear()
