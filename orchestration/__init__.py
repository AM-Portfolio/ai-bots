"""
Orchestration Layer for AI Development Agent

This package contains modular components for processing user messages,
enriching context, building prompts, and executing agent tasks.

Architecture:
- message_parser: Extract references (URLs, tickets, issue IDs)
- context_enricher: Fetch data from GitHub/Jira/Confluence
- prompt_builder: Format enriched context for LLM
- langgraph_agent: Execute tasks with LLM coordination
"""

from orchestration.shared.models import (
    ParsedMessage,
    EnrichedContext,
    PromptTemplate,
    AgentTask
)

__all__ = [
    'ParsedMessage',
    'EnrichedContext',
    'PromptTemplate',
    'AgentTask'
]
