"""
Streaming Wrapper for Orchestration Pipeline

Captures and streams backend processing activity to frontend in real-time
"""
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from datetime import datetime
import json

from orchestration.facade import OrchestrationFacade
from shared.services.manager import ServiceManager
from shared.llm_providers.factory import LLMFactory

logger = logging.getLogger(__name__)


class StreamingOrchestrationWrapper:
    """
    Wrapper around OrchestrationFacade that streams processing logs
    to frontend in real-time using Server-Sent Events
    """
    
    def __init__(
        self,
        service_manager: ServiceManager,
        llm_factory: Optional[LLMFactory] = None
    ):
        self.facade = OrchestrationFacade(service_manager, llm_factory)
        self.activity_log = []
        
    def _emit_activity(self, step: str, status: str, details: Dict[str, Any] = None):
        """Emit activity event"""
        activity = {
            'timestamp': datetime.utcnow().isoformat(),
            'step': step,
            'status': status,
            'details': details or {}
        }
        self.activity_log.append(activity)
        return activity
    
    async def stream_process_message(
        self,
        message: str,
        template_name: str = "default",
        execute_tasks: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Process message and stream backend activity
        
        Yields SSE-formatted events showing what's happening in the backend
        """
        self.activity_log = []
        
        try:
            # Start pipeline
            activity = self._emit_activity(
                "pipeline_start",
                "started",
                {
                    "message_preview": message[:50] + ("..." if len(message) > 50 else ""),
                    "template": template_name
                }
            )
            yield f"data: {json.dumps(activity)}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 1: Parse message
            activity = self._emit_activity(
                "parsing",
                "running",
                {"action": "Extracting GitHub URLs, Jira tickets, Confluence pages..."}
            )
            yield f"data: {json.dumps(activity)}\n\n"
            await asyncio.sleep(0.1)
            
            parsed_message = await self.facade.parser.parse(message)
            
            activity = self._emit_activity(
                "parsing",
                "completed",
                {
                    "references_found": len(parsed_message.references),
                    "github_refs": len([r for r in parsed_message.references if 'github' in r.type.value.lower()]),
                    "jira_refs": len([r for r in parsed_message.references if 'jira' in r.type.value.lower()]),
                    "confluence_refs": len([r for r in parsed_message.references if 'confluence' in r.type.value.lower()])
                }
            )
            yield f"data: {json.dumps(activity)}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 2: Enrich context
            if parsed_message.references:
                activity = self._emit_activity(
                    "enrichment",
                    "running",
                    {
                        "action": f"Fetching data for {len(parsed_message.references)} references...",
                        "references": [r.type.value for r in parsed_message.references]
                    }
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
                
                enriched_context = await self.facade.enricher.enrich(
                    parsed_message,
                    options=kwargs.get('enrich_options', {})
                )
                
                activity = self._emit_activity(
                    "enrichment",
                    "completed",
                    {
                        "context_items": len(enriched_context.context_items),
                        "cache_hits": len([item for item in enriched_context.context_items if item.cache_hit]),
                        "sources": list(set([item.source_type.value for item in enriched_context.context_items]))
                    }
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
            else:
                enriched_context = await self.facade.enricher.enrich(parsed_message)
                activity = self._emit_activity(
                    "enrichment",
                    "skipped",
                    {"reason": "No references found to enrich"}
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
            
            # Step 3: Build prompt
            activity = self._emit_activity(
                "prompt_building",
                "running",
                {
                    "action": f"Formatting prompt with template '{template_name}'...",
                    "template": template_name
                }
            )
            yield f"data: {json.dumps(activity)}\n\n"
            await asyncio.sleep(0.1)
            
            formatted_prompt = await self.facade.prompt_builder.build(
                enriched_context,
                template_name=template_name,
                **kwargs
            )
            
            activity = self._emit_activity(
                "prompt_building",
                "completed",
                {
                    "system_prompt_length": len(formatted_prompt.system_prompt),
                    "user_prompt_length": len(formatted_prompt.user_prompt),
                    "context_included": len(enriched_context.context_items) > 0
                }
            )
            yield f"data: {json.dumps(activity)}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 4: Plan tasks
            if execute_tasks:
                activity = self._emit_activity(
                    "task_planning",
                    "running",
                    {"action": "Analyzing user intent and planning tasks..."}
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
                
                user_intent = kwargs.get('user_intent', message)
                tasks = await self.facade.agent.plan_tasks(enriched_context, user_intent)
                
                activity = self._emit_activity(
                    "task_planning",
                    "completed",
                    {
                        "tasks_planned": len(tasks),
                        "task_types": [task.task_type for task in tasks]
                    }
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 5: Execute tasks
                results = []
                for i, task in enumerate(tasks, 1):
                    activity = self._emit_activity(
                        f"task_execution_{i}",
                        "running",
                        {
                            "action": f"Executing task {i}/{len(tasks)}: {task.task_type}",
                            "task_type": task.task_type,
                            "description": task.description
                        }
                    )
                    yield f"data: {json.dumps(activity)}\n\n"
                    await asyncio.sleep(0.1)
                    
                    completed_task = await self.facade.agent.execute(task)
                    results.append(completed_task)
                    
                    activity = self._emit_activity(
                        f"task_execution_{i}",
                        "completed" if completed_task.status == "completed" else "failed",
                        {
                            "task_type": task.task_type,
                            "status": completed_task.status,
                            "has_result": completed_task.result is not None,
                            "error": completed_task.error if completed_task.status == "failed" else None
                        }
                    )
                    yield f"data: {json.dumps(activity)}\n\n"
                    await asyncio.sleep(0.1)
            else:
                tasks = []
                results = []
                activity = self._emit_activity(
                    "task_execution",
                    "skipped",
                    {"reason": "Task execution disabled"}
                )
                yield f"data: {json.dumps(activity)}\n\n"
                await asyncio.sleep(0.1)
            
            # Pipeline complete
            activity = self._emit_activity(
                "pipeline_complete",
                "completed",
                {
                    "total_duration": sum([
                        (r.completed_at - r.created_at).total_seconds() 
                        for r in results if r.completed_at and r.created_at
                    ]) if results else 0,
                    "references_found": len(parsed_message.references),
                    "context_items": len(enriched_context.context_items),
                    "tasks_executed": len(results),
                    "successful_tasks": len([r for r in results if r.status == "completed"])
                }
            )
            yield f"data: {json.dumps(activity)}\n\n"
            
            # Send final result
            final_result = {
                'parsed_message': {
                    'original': parsed_message.original_message,
                    'references_count': len(parsed_message.references)
                },
                'enriched_context': {
                    'context_items': len(enriched_context.context_items)
                },
                'formatted_prompt': {
                    'system_prompt_length': len(formatted_prompt.system_prompt),
                    'user_prompt_length': len(formatted_prompt.user_prompt)
                },
                'tasks': {
                    'planned': len(tasks),
                    'executed': len(results),
                    'successful': len([r for r in results if r.status == "completed"])
                },
                'activity_log': self.activity_log
            }
            
            yield f"data: {json.dumps({'type': 'final_result', 'result': final_result})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming orchestration failed: {e}", exc_info=True)
            error_activity = self._emit_activity(
                "pipeline_error",
                "failed",
                {
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            yield f"data: {json.dumps(error_activity)}\n\n"
    
    async def get_activity_summary(self) -> Dict[str, Any]:
        """Get summary of backend activity"""
        return {
            'total_steps': len(self.activity_log),
            'completed_steps': len([a for a in self.activity_log if a['status'] == 'completed']),
            'failed_steps': len([a for a in self.activity_log if a['status'] == 'failed']),
            'activity_log': self.activity_log
        }
