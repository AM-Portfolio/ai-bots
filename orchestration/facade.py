"""
Orchestration Facade

Unified interface for the entire orchestration pipeline:
Message Parser → Context Enricher → Prompt Builder → LangGraph Agent
"""
import logging
from typing import Dict, List, Optional, Any
from orchestration.message_parser import MessageParser
from orchestration.context_enricher import ContextEnricher
from orchestration.prompt_builder import PromptBuilder
from orchestration.langgraph_agent import LangGraphAgent
from orchestration.shared.models import (
    ParsedMessage,
    EnrichedContext,
    FormattedPrompt,
    AgentTask
)
from shared.services.manager import ServiceManager
from shared.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class OrchestrationFacade:
    """
    Unified interface for the orchestration pipeline
    
    Usage:
        facade = OrchestrationFacade(service_manager)
        result = await facade.process_message("Analyze issue #123 in repo/name")
    """
    
    def __init__(
        self,
        service_manager: ServiceManager,
        llm_factory: Optional[LLMFactory] = None
    ):
        """
        Initialize orchestration facade
        
        Args:
            service_manager: Service manager for integrations
            llm_factory: LLM factory for generating responses
        """
        self.service_manager = service_manager
        self.llm_factory = llm_factory or LLMFactory()
        
        self.parser = MessageParser()
        self.enricher = ContextEnricher(service_manager)
        self.prompt_builder = PromptBuilder()
        self.agent = LangGraphAgent(service_manager, llm_factory)
    
    async def process_message(
        self,
        message: str,
        template_name: str = "default",
        execute_tasks: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a user message through the entire pipeline
        
        Args:
            message: Raw user message
            template_name: Prompt template to use
            execute_tasks: Whether to execute planned tasks
            **kwargs: Additional parameters
            
        Returns:
            Complete processing result with all pipeline outputs
        """
        logger.info(
            "Starting orchestration pipeline",
            extra={
                "message_length": len(message),
                "template_name": template_name,
                "execute_tasks": execute_tasks
            }
        )
        
        parsed_message = await self.parser.parse(message)
        
        enriched_context = await self.enricher.enrich(
            parsed_message,
            options=kwargs.get('enrich_options', {})
        )
        
        formatted_prompt = await self.prompt_builder.build(
            enriched_context,
            template_name=template_name,
            **kwargs
        )
        
        tasks = []
        results = []
        
        if execute_tasks:
            user_intent = kwargs.get('user_intent', message)
            tasks = await self.agent.plan_tasks(enriched_context, user_intent)
            
            for task in tasks:
                completed_task = await self.agent.execute(task)
                results.append(completed_task)
        
        logger.info(
            "Orchestration pipeline completed",
            extra={
                "references_found": len(parsed_message.references),
                "context_items": len(enriched_context.context_items),
                "tasks_planned": len(tasks),
                "tasks_executed": len(results),
                "successful_tasks": len([r for r in results if r.status == "completed"])
            }
        )
        
        return {
            'parsed_message': parsed_message,
            'enriched_context': enriched_context,
            'formatted_prompt': formatted_prompt,
            'planned_tasks': tasks,
            'task_results': results,
            'metadata': {
                'references_found': len(parsed_message.references),
                'context_items': len(enriched_context.context_items),
                'tasks_executed': len(results)
            }
        }
    
    async def parse_only(self, message: str) -> ParsedMessage:
        """Parse message only (step 1)"""
        return await self.parser.parse(message)
    
    async def enrich_only(
        self,
        parsed_message: ParsedMessage,
        **kwargs
    ) -> EnrichedContext:
        """Enrich parsed message only (step 2)"""
        return await self.enricher.enrich(parsed_message, kwargs)
    
    async def build_prompt_only(
        self,
        enriched_context: EnrichedContext,
        template_name: str = "default",
        **kwargs
    ) -> FormattedPrompt:
        """Build prompt only (step 3)"""
        return await self.prompt_builder.build(
            enriched_context,
            template_name,
            **kwargs
        )
    
    async def execute_task_only(
        self,
        task: AgentTask,
        stream: bool = False
    ) -> AgentTask:
        """Execute single task only (step 4)"""
        return await self.agent.execute(task, stream)
    
    def clear_cache(self):
        """Clear all caches"""
        self.enricher.clear_cache()
    
    def add_custom_template(
        self,
        name: str,
        system: str,
        user: str
    ):
        """Add custom prompt template"""
        self.prompt_builder.add_template(name, system, user)
