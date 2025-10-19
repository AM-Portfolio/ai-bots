"""
Base interfaces for orchestration modules
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from orchestration.shared.models import (
    ParsedMessage,
    EnrichedContext,
    FormattedPrompt,
    AgentTask
)


class IMessageParser(ABC):
    """Interface for message parsing"""
    
    @abstractmethod
    async def parse(self, message: str) -> ParsedMessage:
        """
        Parse a message to extract references
        
        Args:
            message: Raw user message
            
        Returns:
            ParsedMessage with extracted references
        """
        pass


class IContextEnricher(ABC):
    """Interface for context enrichment"""
    
    @abstractmethod
    async def enrich(
        self,
        parsed_message: ParsedMessage,
        options: Optional[Dict[str, Any]] = None
    ) -> EnrichedContext:
        """
        Enrich parsed message with data from external sources
        
        Args:
            parsed_message: Parsed message with references
            options: Optional enrichment options (e.g., depth, sources)
            
        Returns:
            EnrichedContext with fetched data
        """
        pass


class IPromptBuilder(ABC):
    """Interface for prompt building"""
    
    @abstractmethod
    async def build(
        self,
        enriched_context: EnrichedContext,
        template_name: str = "default",
        **kwargs
    ) -> FormattedPrompt:
        """
        Build a formatted prompt from enriched context
        
        Args:
            enriched_context: Enriched context data
            template_name: Name of prompt template to use
            **kwargs: Additional template variables
            
        Returns:
            FormattedPrompt ready for LLM
        """
        pass


class ILangGraphAgent(ABC):
    """Interface for LangGraph agent"""
    
    @abstractmethod
    async def execute(
        self,
        task: AgentTask,
        stream: bool = False
    ) -> AgentTask:
        """
        Execute an agent task
        
        Args:
            task: Task to execute
            stream: Whether to stream responses
            
        Returns:
            Completed task with results
        """
        pass
    
    @abstractmethod
    async def plan_tasks(
        self,
        enriched_context: EnrichedContext,
        user_intent: str
    ) -> List[AgentTask]:
        """
        Plan tasks based on context and user intent
        
        Args:
            enriched_context: Enriched context
            user_intent: User's intended action
            
        Returns:
            List of planned tasks
        """
        pass
