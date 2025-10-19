"""
Example Usage of Orchestration Layer

Demonstrates how to integrate the modular orchestration pipeline
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from orchestration.facade import OrchestrationFacade
from shared.services.manager import ServiceManager
from shared.llm.factory import LLMFactory


router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


class MessageRequest(BaseModel):
    """Request model for message processing"""
    message: str
    template_name: str = "default"
    execute_tasks: bool = True
    enrich_options: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Response model for message processing"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/process", response_model=MessageResponse)
async def process_message(
    request: MessageRequest,
    service_manager: ServiceManager = Depends(),
    llm_factory: LLMFactory = Depends()
):
    """
    Process a message through the orchestration pipeline
    
    Example request:
    {
        "message": "Analyze issue #123 in owner/repo",
        "template_name": "bug_analysis",
        "execute_tasks": true
    }
    """
    try:
        facade = OrchestrationFacade(service_manager, llm_factory)
        
        result = await facade.process_message(
            message=request.message,
            template_name=request.template_name,
            execute_tasks=request.execute_tasks,
            enrich_options=request.enrich_options or {}
        )
        
        serialized_result = {
            'parsed_message': {
                'original': result['parsed_message'].original_message,
                'references': [
                    {
                        'type': ref.type.value,
                        'text': ref.raw_text,
                        'value': ref.normalized_value,
                        'metadata': ref.metadata
                    }
                    for ref in result['parsed_message'].references
                ],
                'clean_message': result['parsed_message'].clean_message
            },
            'enriched_context': {
                'total_items': result['enriched_context'].total_items,
                'context_items': [
                    {
                        'source_type': item.source_type.value,
                        'source_id': item.source_id,
                        'data': item.data,
                        'cache_hit': item.cache_hit
                    }
                    for item in result['enriched_context'].context_items
                ]
            },
            'formatted_prompt': {
                'system_prompt': result['formatted_prompt'].system_prompt,
                'user_prompt': result['formatted_prompt'].user_prompt,
                'context_summary': result['formatted_prompt'].context_summary
            },
            'tasks': [
                {
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'status': task.status,
                    'result': task.result
                }
                for task in result['task_results']
            ],
            'metadata': result['metadata']
        }
        
        return MessageResponse(success=True, data=serialized_result)
    
    except Exception as e:
        return MessageResponse(success=False, error=str(e))


@router.post("/parse-only")
async def parse_only(message: str, service_manager: ServiceManager = Depends()):
    """Parse message only (step 1 of pipeline)"""
    try:
        facade = OrchestrationFacade(service_manager)
        result = await facade.parse_only(message)
        
        return {
            'success': True,
            'data': {
                'original_message': result.original_message,
                'references': [
                    {
                        'type': ref.type.value,
                        'value': ref.normalized_value,
                        'metadata': ref.metadata
                    }
                    for ref in result.references
                ],
                'clean_message': result.clean_message
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint for orchestration layer"""
    return {
        'status': 'healthy',
        'modules': {
            'message_parser': 'operational',
            'context_enricher': 'operational',
            'prompt_builder': 'operational',
            'langgraph_agent': 'operational'
        }
    }


class DirectUsageExample:
    """Example of direct usage without FastAPI"""
    
    @staticmethod
    async def example_1_full_pipeline():
        """Example 1: Full pipeline processing"""
        from shared.services.manager import ServiceManager
        
        service_manager = ServiceManager()
        facade = OrchestrationFacade(service_manager)
        
        result = await facade.process_message(
            message="Fix bug in PROJ-123 and update docs",
            template_name="bug_analysis",
            execute_tasks=True
        )
        
        print(f"Found {len(result['parsed_message'].references)} references")
        print(f"Enriched with {result['metadata']['context_items']} items")
        print(f"Executed {result['metadata']['tasks_executed']} tasks")
        
        return result
    
    @staticmethod
    async def example_2_step_by_step():
        """Example 2: Step-by-step pipeline"""
        from shared.services.manager import ServiceManager
        
        service_manager = ServiceManager()
        facade = OrchestrationFacade(service_manager)
        
        parsed = await facade.parse_only("Check https://github.com/owner/repo/issues/123")
        print(f"Step 1: Found {len(parsed.references)} references")
        
        enriched = await facade.enrich_only(parsed)
        print(f"Step 2: Enriched with {len(enriched.context_items)} items")
        
        prompt = await facade.build_prompt_only(enriched, template_name="default")
        print(f"Step 3: Built prompt with {len(prompt.system_prompt)} chars")
        
        from orchestration.shared.models import AgentTask
        import uuid
        
        task = AgentTask(
            task_id=str(uuid.uuid4()),
            task_type="code_analysis",
            description="Analyze the code",
            context=enriched
        )
        
        result = await facade.execute_task_only(task)
        print(f"Step 4: Task {result.status}")
        
        return result
    
    @staticmethod
    async def example_3_custom_template():
        """Example 3: Using custom template"""
        from shared.services.manager import ServiceManager
        
        service_manager = ServiceManager()
        facade = OrchestrationFacade(service_manager)
        
        facade.add_custom_template(
            name="security_review",
            system="You are a security expert reviewing code for vulnerabilities.",
            user="Review this code:\n{context_section}\n\nUser notes: {user_message}"
        )
        
        result = await facade.process_message(
            message="Check for SQL injection vulnerabilities",
            template_name="security_review"
        )
        
        return result


if __name__ == "__main__":
    import asyncio
    
    print("Running orchestration examples...")
    asyncio.run(DirectUsageExample.example_1_full_pipeline())
