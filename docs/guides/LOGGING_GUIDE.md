# Orchestration Layer Logging Guide

## Overview
The orchestration layer now includes comprehensive structured logging for complete observability across the entire message processing pipeline.

## Logging Structure

### Log Levels
- **INFO:** Major operations (pipeline start/completion, module entry/exit)
- **DEBUG:** Detailed flow information (reference types, cache hits, task planning)
- **ERROR:** Operation failures with full stack traces (exc_info=True)

### Structured Logging
All log messages use structured `extra` dictionaries with contextual metadata for easy parsing and filtering:

```python
logger.info(
    "Message parsed successfully",
    extra={
        "reference_count": 3,
        "message_length": 150,
        "processing_time_ms": 45
    }
)
```

## Pipeline Log Flow

### 1. OrchestrationFacade (Entry Point)
```
INFO: Starting orchestration pipeline
  - message_length: 150
  - template_name: "bug_analysis"
  - execute_tasks: true

INFO: Orchestration pipeline completed
  - references_found: 3
  - context_items: 5
  - tasks_planned: 2
  - tasks_executed: 2
  - successful_tasks: 2
```

### 2. Message Parser
```
INFO: Starting message parsing
  - message_length: 150

DEBUG: Extracted references by type
  - github_urls: 2
  - github_issues: 0
  - jira_tickets: 1
  - confluence_urls: 0

INFO: Message parsing completed
  - total_references: 3
```

### 3. Context Enricher
```
INFO: Starting context enrichment
  - reference_count: 3
  - use_cache: true
  - max_depth: 2

DEBUG: Processing reference
  - type: "github_url"
  - value: "owner/repo"

ERROR: Error enriching GitHub reference (if failure)
  - reference_type: "github_url"
  - reference_value: "owner/repo"
  - owner: "owner"
  - repo: "repo"
  - issue_number: "123"
  - error: "Service unavailable"
  - exc_info: <stack trace>

INFO: Context enrichment completed
  - items_fetched: 5
  - cache_hits: 2
```

### 4. Prompt Builder
```
INFO: Starting prompt building
  - template_name: "bug_analysis"
  - context_items: 5
  - references: 3

INFO: Prompt building completed
  - system_prompt_length: 250
  - user_prompt_length: 1500
  - context_summary_length: 800
```

### 5. LangGraph Agent

**Task Planning:**
```
INFO: Starting task planning
  - user_intent: "Fix bug in issue #123"
  - context_items: 5

INFO: Task planning completed
  - tasks_planned: 2
  - task_types: ["bug_diagnosis", "code_analysis"]
```

**Task Execution:**
```
INFO: Starting task execution
  - task_id: "uuid-1234"
  - task_type: "bug_diagnosis"
  - description: "Analyze bug and suggest fix"

INFO: Task execution completed
  - task_id: "uuid-1234"
  - task_type: "bug_diagnosis"
  - status: "completed"

ERROR: Task execution failed (if failure)
  - task_id: "uuid-1234"
  - task_type: "bug_diagnosis"
  - error: "LLM timeout"
  - exc_info: <stack trace>
```

## Accessing Logs

### In Development
Logs are written to stdout and captured by the workflow:

```bash
# View workflow logs
cat /tmp/logs/AI_Dev_Agent_*.log

# Search for errors
grep "ERROR" /tmp/logs/AI_Dev_Agent_*.log

# Filter by module
grep "orchestration.message_parser" /tmp/logs/AI_Dev_Agent_*.log
```

### In Python Code
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Use the orchestration layer
from orchestration.facade import OrchestrationFacade

facade = OrchestrationFacade(service_manager)
result = await facade.process_message("Analyze issue #123")

# Logs will automatically appear in stdout
```

### Advanced Filtering
```python
import logging.config

# Configure with JSON formatter for structured logging
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Troubleshooting with Logs

### Scenario 1: No References Found
```
INFO: Message parsing completed - total_references: 0
```
**Action:** Check message format - GitHub URLs, Jira tickets may not match regex patterns.

### Scenario 2: Context Enrichment Failures
```
ERROR: Error enriching GitHub reference
  - owner: "myorg"
  - repo: "myrepo"
  - error: "Repository not found"
```
**Action:** Verify GitHub service is connected and has access to the repository.

### Scenario 3: Cache Performance
```
INFO: Context enrichment completed
  - items_fetched: 10
  - cache_hits: 8
```
**Insight:** 80% cache hit rate - good performance. Low cache hits may indicate varied references or cache cleared frequently.

### Scenario 4: Task Execution Failures
```
ERROR: Task execution failed
  - task_type: "bug_diagnosis"
  - error: "LLM API timeout"
```
**Action:** Check LLM service availability, increase timeout, or implement retry logic.

## Best Practices

### 1. Log Early, Log Often
Every major operation should have entry/exit logs:
```python
logger.info("Starting operation", extra={"input_size": len(data)})
try:
    result = process(data)
    logger.info("Operation completed", extra={"result_size": len(result)})
except Exception as e:
    logger.error("Operation failed", extra={"error": str(e)}, exc_info=True)
    raise
```

### 2. Use Structured Metadata
Always include relevant context in `extra` dictionaries:
```python
# Good
logger.info(
    "Processing reference",
    extra={"type": ref.type, "value": ref.value, "cache_hit": True}
)

# Bad
logger.info(f"Processing {ref.type} reference {ref.value}")
```

### 3. Don't Log Secrets
Never log sensitive information:
```python
# Bad
logger.info("API request", extra={"api_key": secret_key})

# Good
logger.info("API request", extra={"api_key_prefix": secret_key[:8] + "..."})
```

### 4. Use Appropriate Levels
- **DEBUG:** Verbose details needed only during development
- **INFO:** Normal operational events (pipeline steps)
- **WARNING:** Degraded functionality but recoverable
- **ERROR:** Operation failures requiring attention

## Future Enhancements

### Correlation IDs (Planned)
Track requests across the entire pipeline:
```python
import uuid

correlation_id = str(uuid.uuid4())

logger.info(
    "Starting pipeline",
    extra={"correlation_id": correlation_id}
)

# Pass correlation_id through all modules
# All logs for this request will share the same correlation_id
```

### Metrics Integration (Planned)
Export log metrics to Prometheus:
```python
from prometheus_client import Counter, Histogram

pipeline_requests = Counter('pipeline_requests_total', 'Total pipeline requests')
pipeline_duration = Histogram('pipeline_duration_seconds', 'Pipeline duration')

with pipeline_duration.time():
    result = await facade.process_message(message)
    pipeline_requests.inc()
```

### OpenTelemetry Tracing (Planned)
Full distributed tracing across services:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_message"):
    with tracer.start_as_current_span("parse"):
        parsed = await parser.parse(message)
    with tracer.start_as_current_span("enrich"):
        enriched = await enricher.enrich(parsed)
    # etc.
```

## Summary

The orchestration layer now provides:
- ✅ Structured logging at every layer
- ✅ Contextual metadata in all log messages
- ✅ Proper error handling with stack traces
- ✅ Pipeline flow visibility from start to completion
- ✅ Cache hit rate tracking
- ✅ Task execution status monitoring
- ✅ Easy troubleshooting with detailed error information

This logging infrastructure provides complete observability for debugging, monitoring, and optimizing the orchestration pipeline.
