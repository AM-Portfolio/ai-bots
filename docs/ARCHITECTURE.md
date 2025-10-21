# Architecture Philosophy & Design Principles

## Core Philosophy: Modular, Scalable, Maintainable

This project follows a **modular-first** approach where every component is designed to be:
- **Independent:** Each module can be developed, tested, and maintained separately
- **Scalable:** Easy to extend with new features without touching existing code
- **Composable:** Modules work together through well-defined interfaces
- **Observable:** Comprehensive logging and metrics at every layer

## Design Principles

### 1. **Small, Focused Methods**
Every method should do **one thing well**. We prefer many small methods over large monolithic functions.

**✅ Good Example:**
```python
class ContextEnricher:
    async def enrich(self, parsed_message: ParsedMessage) -> EnrichedContext:
        """Orchestrates enrichment - delegates to specialized methods"""
        context_items = []
        for reference in parsed_message.references:
            items = await self._enrich_single_reference(reference)
            context_items.extend(items)
        return EnrichedContext(context_items=context_items)
    
    async def _enrich_single_reference(self, ref: Reference) -> List[ContextData]:
        """Handles one reference - delegates by type"""
        if ref.type == ReferenceType.GITHUB_URL:
            return await self._enrich_github_reference(ref)
        elif ref.type == ReferenceType.JIRA_TICKET:
            return await self._enrich_jira_reference(ref)
        # etc.
    
    async def _enrich_github_reference(self, ref: Reference) -> List[ContextData]:
        """Focused on GitHub enrichment only"""
        # Single responsibility: fetch GitHub data
```

**❌ Bad Example:**
```python
async def enrich(self, parsed_message: ParsedMessage) -> EnrichedContext:
    """500 lines doing everything: parsing, fetching, caching, error handling"""
    # Too much responsibility in one method!
```

### 2. **Interface-Driven Design**
All major components define abstract interfaces, making them easy to mock, test, and swap implementations.

```python
# orchestration/shared/interfaces.py
class IMessageParser(ABC):
    @abstractmethod
    async def parse(self, message: str) -> ParsedMessage:
        """Contract: parse message → return structured references"""
        pass

# Easy to add new implementation without changing consumers
class RegexMessageParser(IMessageParser):
    """Regex-based implementation"""
    pass

class LLMMessageParser(IMessageParser):
    """Future: LLM-based implementation"""
    pass
```

### 3. **Dataclass-First Models**
Use typed dataclasses for all data transfer objects. This provides:
- Type safety with IDE autocomplete
- Clear contracts between modules
- Easy serialization for APIs
- Self-documenting code

```python
@dataclass
class Reference:
    type: ReferenceType
    raw_text: str
    normalized_value: str
    metadata: Dict[str, Any]
    position: int

# Clear, typed, immutable data structure
```

### 4. **Layered Architecture**

```
┌─────────────────────────────────────────┐
│         Interfaces Layer                │  FastAPI, Teams Bot, Webhooks
│  (API endpoints, bot handlers)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Orchestration Layer                │  Message processing pipeline
│  Parser → Enricher → Builder → Agent    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Features Layer                  │  Bug analysis, doc generation
│  (Business logic, workflows)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Services Layer                  │  GitHub, Jira, Confluence
│  (External integrations)                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Infrastructure Layer               │  Database, LLM, Monitoring
│  (Shared utilities, clients)            │
└─────────────────────────────────────────┘
```

Each layer only depends on layers below it. **Never reach up the stack.**

### 5. **Facade Pattern for Simplicity**
Complex subsystems expose simple facades for consumers.

```python
# Complex: manually orchestrate 4 modules
parser = MessageParser()
enricher = ContextEnricher(service_manager)
builder = PromptBuilder()
agent = LangGraphAgent(llm_factory)

parsed = await parser.parse(message)
enriched = await enricher.enrich(parsed)
prompt = await builder.build(enriched)
result = await agent.execute(prompt)

# Simple: use facade
facade = OrchestrationFacade(service_manager, llm_factory)
result = await facade.process_message(message)
```

### 6. **Comprehensive Logging**
Every module includes structured logging for observability:

```python
import logging
logger = logging.getLogger(__name__)

class ContextEnricher:
    async def enrich(self, parsed_message: ParsedMessage) -> EnrichedContext:
        logger.info(
            "Starting context enrichment",
            extra={
                "reference_count": len(parsed_message.references),
                "message_length": len(parsed_message.original_message)
            }
        )
        
        try:
            # ... enrichment logic
            logger.info(
                "Context enrichment completed",
                extra={"items_fetched": len(context_items)}
            )
        except Exception as e:
            logger.error(
                "Context enrichment failed",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
```

## Architecture Patterns Used

### 1. Repository Pattern (Data Layer)
```python
class ConversationRepository:
    """Abstracts database operations"""
    async def create(self, conversation: Conversation) -> Conversation:
        pass
    
    async def get_by_id(self, id: str) -> Optional[Conversation]:
        pass
```

### 2. Factory Pattern (LLM Providers)
```python
class LLMFactory:
    """Creates LLM clients with automatic fallback"""
    def create_client(self, provider: str = "together") -> BaseLLM:
        if provider == "together":
            return TogetherAIClient()
        elif provider == "azure":
            return AzureOpenAIClient()
```

### 3. Strategy Pattern (Prompt Templates)
```python
class PromptBuilder:
    def __init__(self):
        self.templates = {
            "default": DefaultTemplate(),
            "bug_analysis": BugAnalysisTemplate(),
            "documentation": DocumentationTemplate()
        }
    
    def build(self, context: EnrichedContext, template_name: str):
        template = self.templates[template_name]
        return template.format(context)
```

### 4. Service Layer Pattern (External Integrations)
```python
class BaseService(ABC):
    """Base class for all external services"""
    @abstractmethod
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        pass

class GitHubService(BaseService):
    """GitHub-specific implementation"""
    pass
```

## Scaling Guidelines

### Adding a New Service Integration

**Step 1:** Create service class
```python
# shared/services/implementations/new_service.py
class NewService(BaseService):
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        # Implement service operations
        pass
```

**Step 2:** Register with ServiceManager
```python
# shared/services/manager.py
service_manager.register_service("new_service", NewService())
```

**Step 3:** Add enrichment support (optional)
```python
# orchestration/context_enricher/implementations/enricher.py
async def _enrich_new_service_reference(self, ref: Reference):
    service = self.service_manager.get_service("new_service")
    data = await service.execute("fetch_data", id=ref.normalized_value)
    return [ContextData(source_type=ContextSourceType.NEW_SERVICE, data=data)]
```

### Adding a New Prompt Template

```python
# orchestration/prompt_builder/implementations/builder.py
self.templates["security_review"] = PromptTemplate(
    system_prompt="You are a security expert...",
    user_prompt_template="Review for vulnerabilities:\n{context_section}"
)
```

### Adding a New Task Type

```python
# orchestration/langgraph_agent/implementations/agent.py
async def _execute_security_audit_task(self, task: AgentTask) -> AgentTask:
    """Execute security audit task"""
    # Task-specific logic
    task.status = "completed"
    task.result = {"findings": [...]}
    return task
```

## Code Metrics & Quality

### Module Size Guidelines
- **Maximum file size:** 250 lines per module
- **Maximum method size:** 30 lines per method
- **Cyclomatic complexity:** <10 per method

### Current Metrics
```
Service Layer:
- BaseService: ~85 lines
- ServiceManager: ~145 lines
- GitHubService: ~240 lines
- Average: ~157 lines/service

Orchestration Layer:
- MessageParser: ~180 lines
- ContextEnricher: ~200 lines
- PromptBuilder: ~190 lines
- LangGraphAgent: ~220 lines
- OrchestrationFacade: ~140 lines
- Total: ~767 lines (5 modules)
```

### Testing Strategy
```
Unit Tests:
- Test each module in isolation
- Mock all dependencies
- Test edge cases and error paths

Integration Tests:
- Test module interactions
- Use real ServiceManager (with mocked services)
- Test full pipeline flows

End-to-End Tests:
- Test complete workflows
- Use test database
- Test API endpoints
```

## File Organization

### Standard Module Structure
```
module_name/
├── implementations/          # Concrete implementations
│   ├── __init__.py
│   └── implementation.py    # Main implementation
├── interfaces/              # Abstract interfaces (optional)
├── models/                  # Data models (optional)
└── __init__.py             # Public API exports
```

### Benefits of This Structure
1. **Clear separation:** Interface vs implementation
2. **Easy testing:** Mock interfaces in tests
3. **Extensibility:** Add new implementations without touching old code
4. **Discoverability:** Clear where to find things

## Performance Considerations

### Caching Strategy
```python
class ContextEnricher:
    def __init__(self):
        self.cache: Dict[str, ContextData] = {}
    
    async def _get_cached_or_fetch(self, key: str, fetch_fn):
        if key in self.cache:
            logger.debug("Cache hit", extra={"key": key})
            return self.cache[key]
        
        data = await fetch_fn()
        self.cache[key] = data
        return data
```

### Async/Await Throughout
All I/O operations are async to avoid blocking:
- Database queries
- HTTP requests
- LLM API calls
- File operations

### Connection Pooling
ServiceManager maintains connection pools for reuse:
```python
class ServiceManager:
    def __init__(self):
        self.services: Dict[str, BaseService] = {}  # Pool of services
        self.llm_wrapper = ServiceLLMWrapper()      # Shared LLM wrapper
```

## Observability

### Logging Levels
- **DEBUG:** Detailed flow information, cache hits/misses
- **INFO:** Major operations (enrichment started, tasks completed)
- **WARNING:** Recoverable errors, fallbacks triggered
- **ERROR:** Operation failures, exceptions

### Structured Logging
Always include context in logs:
```python
logger.info(
    "Message parsed successfully",
    extra={
        "reference_count": len(references),
        "message_id": message_id,
        "processing_time_ms": elapsed_ms
    }
)
```

### Metrics (Future)
- Request counts per endpoint
- Processing time distributions
- Cache hit rates
- LLM token usage
- Error rates by service

## Common Pitfalls to Avoid

### ❌ Don't: Large God Classes
```python
class Orchestrator:
    def process_everything(self):
        # 1000 lines doing parsing, enrichment, prompting, execution
        pass
```

### ✅ Do: Small, Focused Classes
```python
class MessageParser: ...      # One responsibility
class ContextEnricher: ...    # One responsibility
class PromptBuilder: ...      # One responsibility
class OrchestrationFacade:    # Composes the above
    def process_message(self):
        parsed = self.parser.parse()
        enriched = self.enricher.enrich(parsed)
        # etc.
```

### ❌ Don't: Tight Coupling
```python
class Enricher:
    def __init__(self):
        self.github = GitHubClient()  # Hard dependency
```

### ✅ Do: Dependency Injection
```python
class Enricher:
    def __init__(self, service_manager: ServiceManager):
        self.service_manager = service_manager  # Can inject mock
```

### ❌ Don't: Silent Failures
```python
try:
    data = await fetch_data()
except Exception:
    pass  # Error swallowed!
```

### ✅ Do: Explicit Error Handling
```python
try:
    data = await fetch_data()
except ServiceError as e:
    logger.error("Fetch failed", extra={"error": str(e)})
    raise  # Propagate or handle appropriately
```

## Summary

**This architecture prioritizes:**
1. 🧩 **Modularity** - Independent, composable components
2. 📈 **Scalability** - Easy to extend without modification
3. 🧪 **Testability** - Interfaces enable mocking
4. 📊 **Observability** - Logging at every layer
5. 🎯 **Simplicity** - Small methods, clear responsibilities
6. 🔒 **Type Safety** - Dataclasses and type hints throughout

**When adding new features, always ask:**
- Can this be a separate module?
- Is this method doing one thing?
- Can I test this in isolation?
- Have I added logging?
- Does this follow our patterns?
