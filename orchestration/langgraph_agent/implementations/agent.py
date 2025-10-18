"""
LangGraph Agent Implementation

Coordinates task execution using LLM-powered workflow
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from orchestration.shared.interfaces import ILangGraphAgent
from orchestration.shared.models import (
    EnrichedContext,
    AgentTask,
    ContextSourceType
)
from shared.services.manager import ServiceManager
from shared.llm.factory import LLMFactory


class LangGraphAgent(ILangGraphAgent):
    """Executes tasks with LLM coordination and workflow management"""
    
    def __init__(
        self,
        service_manager: ServiceManager,
        llm_factory: Optional[LLMFactory] = None
    ):
        """
        Initialize LangGraph agent
        
        Args:
            service_manager: Service manager for integrations
            llm_factory: LLM factory for generating responses
        """
        self.service_manager = service_manager
        self.llm_factory = llm_factory or LLMFactory()
        self.task_registry: Dict[str, AgentTask] = {}
    
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
        task.status = "running"
        self.task_registry[task.task_id] = task
        
        try:
            if task.task_type == "code_analysis":
                result = await self._execute_code_analysis(task)
            elif task.task_type == "bug_diagnosis":
                result = await self._execute_bug_diagnosis(task)
            elif task.task_type == "documentation_generation":
                result = await self._execute_documentation(task)
            elif task.task_type == "code_generation":
                result = await self._execute_code_generation(task)
            else:
                result = await self._execute_generic_task(task)
            
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.utcnow()
        
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()
        
        return task
    
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
        tasks = []
        
        has_github = any(
            item.source_type in [
                ContextSourceType.GITHUB_REPOSITORY,
                ContextSourceType.GITHUB_ISSUE
            ]
            for item in enriched_context.context_items
        )
        
        has_jira = any(
            item.source_type == ContextSourceType.JIRA_ISSUE
            for item in enriched_context.context_items
        )
        
        intent_lower = user_intent.lower()
        
        if 'bug' in intent_lower or 'fix' in intent_lower or 'issue' in intent_lower:
            tasks.append(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="bug_diagnosis",
                description="Analyze bug and suggest fix",
                context=enriched_context,
                parameters={'include_tests': True}
            ))
        
        if 'document' in intent_lower or 'docs' in intent_lower:
            tasks.append(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="documentation_generation",
                description="Generate documentation",
                context=enriched_context,
                parameters={'format': 'markdown'}
            ))
        
        if 'code' in intent_lower or 'implement' in intent_lower:
            tasks.append(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="code_generation",
                description="Generate code implementation",
                context=enriched_context
            ))
        
        if 'analyze' in intent_lower or 'review' in intent_lower:
            tasks.append(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="code_analysis",
                description="Analyze code and provide insights",
                context=enriched_context
            ))
        
        if not tasks:
            tasks.append(AgentTask(
                task_id=str(uuid.uuid4()),
                task_type="generic",
                description="Process user request",
                context=enriched_context
            ))
        
        return tasks
    
    async def _execute_code_analysis(self, task: AgentTask) -> Dict[str, Any]:
        """Execute code analysis task"""
        llm = self.llm_factory.create_llm()
        
        prompt = f"""Analyze the following code context:

{self._format_context_for_llm(task.context)}

Provide:
1. Code quality assessment
2. Potential issues or bugs
3. Improvement suggestions
4. Security considerations
"""
        
        response = await llm.generate(prompt)
        
        return {
            'analysis': response,
            'task_type': 'code_analysis'
        }
    
    async def _execute_bug_diagnosis(self, task: AgentTask) -> Dict[str, Any]:
        """Execute bug diagnosis task"""
        llm = self.llm_factory.create_llm()
        
        prompt = f"""Diagnose this bug:

{self._format_context_for_llm(task.context)}

Provide:
1. Root cause analysis
2. Suggested fix with code
3. Test recommendations
4. Prevention strategies
"""
        
        response = await llm.generate(prompt)
        
        return {
            'diagnosis': response,
            'task_type': 'bug_diagnosis'
        }
    
    async def _execute_documentation(self, task: AgentTask) -> Dict[str, Any]:
        """Execute documentation generation task"""
        llm = self.llm_factory.create_llm()
        
        doc_format = task.parameters.get('format', 'markdown')
        
        prompt = f"""Generate comprehensive documentation in {doc_format} format:

{self._format_context_for_llm(task.context)}

Include:
1. Overview
2. Usage examples
3. API reference
4. Configuration details
"""
        
        response = await llm.generate(prompt)
        
        return {
            'documentation': response,
            'format': doc_format,
            'task_type': 'documentation_generation'
        }
    
    async def _execute_code_generation(self, task: AgentTask) -> Dict[str, Any]:
        """Execute code generation task"""
        llm = self.llm_factory.create_llm()
        
        prompt = f"""Generate code based on this context:

{self._format_context_for_llm(task.context)}

Requirements:
{task.description}

Provide:
1. Complete working code
2. Comments explaining key sections
3. Usage examples
"""
        
        response = await llm.generate(prompt)
        
        return {
            'code': response,
            'task_type': 'code_generation'
        }
    
    async def _execute_generic_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute generic task"""
        llm = self.llm_factory.create_llm()
        
        prompt = f"""Task: {task.description}

Context:
{self._format_context_for_llm(task.context)}

Please complete this task comprehensively.
"""
        
        response = await llm.generate(prompt)
        
        return {
            'response': response,
            'task_type': 'generic'
        }
    
    def _format_context_for_llm(self, context: EnrichedContext) -> str:
        """Format enriched context for LLM prompt"""
        parts = []
        
        parts.append(f"User Message: {context.parsed_message.original_message}\n")
        
        if context.context_items:
            parts.append("Enriched Context:")
            for item in context.context_items:
                parts.append(f"\n{item.source_type.value}:")
                parts.append(str(item.data))
        
        return '\n'.join(parts)
    
    def get_task_status(self, task_id: str) -> Optional[AgentTask]:
        """Get status of a task"""
        return self.task_registry.get(task_id)
