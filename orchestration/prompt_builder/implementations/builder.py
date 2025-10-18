"""
Prompt Builder Implementation

Formats enriched context into structured prompts for LLM consumption
"""
import logging
from typing import Dict, Any
from orchestration.shared.interfaces import IPromptBuilder
from orchestration.shared.models import (
    EnrichedContext,
    FormattedPrompt,
    ContextSourceType
)

logger = logging.getLogger(__name__)


class PromptBuilder(IPromptBuilder):
    """Builds formatted prompts from enriched context"""
    
    def __init__(self):
        self.templates = {
            'default': {
                'system': """You are an AI development agent that helps with software development tasks.
You have access to information from GitHub, Jira, and Confluence.
Provide helpful, accurate responses based on the context provided.""",
                'user': """User Request: {user_message}

{context_section}

Please assist with the user's request using the provided context."""
            },
            'bug_analysis': {
                'system': """You are an expert software engineer specializing in bug analysis and resolution.
Analyze the provided issue details and suggest appropriate fixes.""",
                'user': """Analyze this bug:

User Description: {user_message}

{context_section}

Provide:
1. Root cause analysis
2. Suggested fix
3. Test recommendations"""
            },
            'documentation': {
                'system': """You are a technical documentation expert.
Create clear, comprehensive documentation based on code and requirements.""",
                'user': """Documentation Request: {user_message}

{context_section}

Generate well-structured documentation."""
            },
            'code_review': {
                'system': """You are a senior software engineer performing code review.
Provide constructive feedback on code quality, security, and best practices.""",
                'user': """Review this code:

{context_section}

User Notes: {user_message}

Provide detailed code review feedback."""
            }
        }
    
    async def build(
        self,
        enriched_context: EnrichedContext,
        template_name: str = "default",
        **kwargs
    ) -> FormattedPrompt:
        """
        Build formatted prompt from enriched context
        
        Args:
            enriched_context: Enriched context data
            template_name: Name of template to use
            **kwargs: Additional template variables
            
        Returns:
            FormattedPrompt ready for LLM
        """
        logger.info(
            "Starting prompt building",
            extra={
                "template_name": template_name,
                "context_items": len(enriched_context.context_items),
                "references": len(enriched_context.parsed_message.references)
            }
        )
        
        template = self.templates.get(template_name, self.templates['default'])
        
        system_prompt = template['system']
        
        context_section = self._build_context_section(enriched_context)
        
        user_message = kwargs.get(
            'user_message',
            enriched_context.parsed_message.original_message
        )
        
        user_prompt = template['user'].format(
            user_message=user_message,
            context_section=context_section,
            **kwargs
        )
        
        context_summary = self._build_context_summary(enriched_context)
        
        logger.info(
            "Prompt building completed",
            extra={
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
                "context_summary_length": len(context_summary)
            }
        )
        
        return FormattedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_summary=context_summary,
            metadata={
                'template_name': template_name,
                'context_items_count': len(enriched_context.context_items),
                'references_count': len(enriched_context.parsed_message.references)
            }
        )
    
    def _build_context_section(self, enriched_context: EnrichedContext) -> str:
        """Build formatted context section from enriched data"""
        if not enriched_context.context_items:
            return "No additional context available."
        
        sections = []
        sections.append("## Context Information\n")
        
        github_repos = [
            item for item in enriched_context.context_items
            if item.source_type == ContextSourceType.GITHUB_REPOSITORY
        ]
        if github_repos:
            sections.append("### GitHub Repositories")
            for item in github_repos:
                data = item.data
                sections.append(f"""
**{data.get('name')}**
- Description: {data.get('description', 'N/A')}
- Language: {data.get('language', 'N/A')}
- Stars: {data.get('stars', 0)}
- URL: {data.get('url')}
""")
        
        github_issues = [
            item for item in enriched_context.context_items
            if item.source_type == ContextSourceType.GITHUB_ISSUE
        ]
        if github_issues:
            sections.append("\n### GitHub Issues")
            for item in github_issues:
                data = item.data
                labels = ', '.join(data.get('labels', []))
                sections.append(f"""
**Issue: {data.get('title')}**
- State: {data.get('state')}
- Labels: {labels or 'None'}
- Description: {(data.get('body') or 'No description')[:500]}...
- URL: {data.get('url')}
""")
        
        jira_issues = [
            item for item in enriched_context.context_items
            if item.source_type == ContextSourceType.JIRA_ISSUE
        ]
        if jira_issues:
            sections.append("\n### Jira Tickets")
            for item in jira_issues:
                data = item.data
                sections.append(f"""
**{data.get('key')}: {data.get('summary')}**
- Status: {data.get('status')}
- Priority: {data.get('priority')}
- Type: {data.get('issue_type')}
- Assignee: {data.get('assignee', 'Unassigned')}
- Description: {(data.get('description') or 'No description')[:500]}...
""")
        
        confluence_pages = [
            item for item in enriched_context.context_items
            if item.source_type == ContextSourceType.CONFLUENCE_PAGE
        ]
        if confluence_pages:
            sections.append("\n### Confluence Pages")
            for item in confluence_pages:
                data = item.data
                sections.append(f"""
**{data.get('title')}**
- Space: {data.get('space')}
- Content Preview: {(data.get('content') or 'No content')[:500]}...
- URL: {data.get('url')}
""")
        
        return '\n'.join(sections)
    
    def _build_context_summary(self, enriched_context: EnrichedContext) -> str:
        """Build brief context summary"""
        counts = {
            'repos': 0,
            'issues': 0,
            'prs': 0,
            'jira': 0,
            'confluence': 0
        }
        
        for item in enriched_context.context_items:
            if item.source_type == ContextSourceType.GITHUB_REPOSITORY:
                counts['repos'] += 1
            elif item.source_type == ContextSourceType.GITHUB_ISSUE:
                counts['issues'] += 1
            elif item.source_type == ContextSourceType.GITHUB_PR:
                counts['prs'] += 1
            elif item.source_type == ContextSourceType.JIRA_ISSUE:
                counts['jira'] += 1
            elif item.source_type == ContextSourceType.CONFLUENCE_PAGE:
                counts['confluence'] += 1
        
        parts = []
        if counts['repos']:
            parts.append(f"{counts['repos']} repository/repositories")
        if counts['issues']:
            parts.append(f"{counts['issues']} GitHub issue(s)")
        if counts['prs']:
            parts.append(f"{counts['prs']} PR(s)")
        if counts['jira']:
            parts.append(f"{counts['jira']} Jira ticket(s)")
        if counts['confluence']:
            parts.append(f"{counts['confluence']} Confluence page(s)")
        
        if not parts:
            return "No context enrichment"
        
        return f"Context includes: {', '.join(parts)}"
    
    def add_template(self, name: str, system: str, user: str):
        """Add a custom prompt template"""
        self.templates[name] = {
            'system': system,
            'user': user
        }
