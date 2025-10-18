# Orchestration Layer

Modular, scalable architecture for processing user messages through an AI-powered pipeline.

## Architecture

```
User Message (Teams)
        ↓
[1] 🧩 Message Parser → Extract raw references (URLs, tickets)
        ↓
[2] 📦 Context Enricher → Fetch real data from GitHub/Jira/Confluence
        ↓
[3] 🧠 Prompt Builder → Format for LLM
        ↓
[4] 🔄 LangGraph Agent → Execute small tasks
```

## Modules

### 1. Message Parser
**Location:** `orchestration/message_parser/`

Extracts structured references from user messages:
- GitHub URLs and issue references (#123)
- Jira ticket IDs (PROJ-123)
- Confluence page URLs
- Generic URLs

**Example:**
```python
from orchestration.message_parser import MessageParser

parser = MessageParser()
parsed = await parser.parse("Fix issue #123 in owner/repo")
# Returns: ParsedMessage with references extracted
```

### 2. Context Enricher
**Location:** `orchestration/context_enricher/`

Fetches data from external services based on parsed references:
- GitHub: repository info, issues, PRs
- Jira: ticket details
- Confluence: page content
- Built-in caching for performance

**Example:**
```python
from orchestration.context_enricher import ContextEnricher

enricher = ContextEnricher(service_manager)
context = await enricher.enrich(parsed_message)
# Returns: EnrichedContext with fetched data
```

### 3. Prompt Builder
**Location:** `orchestration/prompt_builder/`

Formats enriched context into structured prompts for LLM:
- Multiple templates: default, bug_analysis, documentation, code_review
- Custom template support
- Context formatting and summarization

**Example:**
```python
from orchestration.prompt_builder import PromptBuilder

builder = PromptBuilder()
prompt = await builder.build(enriched_context, template_name="bug_analysis")
# Returns: FormattedPrompt ready for LLM
```

### 4. LangGraph Agent
**Location:** `orchestration/langgraph_agent/`

Executes tasks with LLM coordination:
- Task planning based on context
- Multiple task types: code_analysis, bug_diagnosis, documentation, code_generation
- Task status tracking

**Example:**
```python
from orchestration.langgraph_agent import LangGraphAgent

agent = LangGraphAgent(service_manager, llm_factory)
tasks = await agent.plan_tasks(enriched_context, "fix bug")
result = await agent.execute(tasks[0])
# Returns: Completed AgentTask with results
```

## Orchestration Facade

**Location:** `orchestration/facade.py`

Unified interface for the entire pipeline:

```python
from orchestration.facade import OrchestrationFacade

facade = OrchestrationFacade(service_manager)

# Full pipeline
result = await facade.process_message("Analyze issue #123 in owner/repo")

# Individual steps
parsed = await facade.parse_only(message)
enriched = await facade.enrich_only(parsed)
prompt = await facade.build_prompt_only(enriched)
```

## Data Models

**Location:** `orchestration/shared/models.py`

Core data models:
- `ParsedMessage`: Parsed message with references
- `EnrichedContext`: Message with fetched external data
- `FormattedPrompt`: LLM-ready prompt
- `AgentTask`: Task definition and results

## Interfaces

**Location:** `orchestration/shared/interfaces.py`

Abstract interfaces for all modules:
- `IMessageParser`
- `IContextEnricher`
- `IPromptBuilder`
- `ILangGraphAgent`

## Integration

### With Existing Code

The orchestration layer integrates with:
- **ServiceManager:** For accessing GitHub/Jira/Confluence services
- **LLMFactory:** For LLM generation
- **Features:** Can be called from `features/` modules

### Example Integration

```python
# In a FastAPI endpoint
from orchestration.facade import OrchestrationFacade

@router.post("/process")
async def process_message(request: MessageRequest):
    facade = OrchestrationFacade(service_manager, llm_factory)
    result = await facade.process_message(
        message=request.message,
        template_name="bug_analysis",
        execute_tasks=True
    )
    return result
```

## Benefits

✅ **Modular:** Each component is independently testable and maintainable

✅ **Scalable:** Easy to add new enrichers, templates, or task types

✅ **Flexible:** Use full pipeline or individual modules

✅ **Cached:** Context enrichment includes intelligent caching

✅ **Type-Safe:** Full TypedDict and interface definitions

## Testing

Each module includes its own tests:
```bash
pytest orchestration/message_parser/tests/
pytest orchestration/context_enricher/tests/
pytest orchestration/prompt_builder/tests/
pytest orchestration/langgraph_agent/tests/
```

## Extension

### Adding a New Enricher

1. Create implementation in `context_enricher/implementations/`
2. Implement `IContextEnricher` interface
3. Register in facade

### Adding a New Task Type

1. Add task type to `AgentTask` model
2. Implement handler in `LangGraphAgent._execute_*`
3. Add to task planning logic

### Adding a New Template

```python
facade.add_custom_template(
    name="my_template",
    system="System prompt...",
    user="User prompt with {user_message} and {context_section}"
)
```
