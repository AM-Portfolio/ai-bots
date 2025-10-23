"""
Code Intelligence System

A modular code analysis and embedding system for semantic code search,
repository understanding, and intelligent code navigation.

## Architecture

### Core Pipeline (core/)
- `embed_repo.py` - Pure embedding generation pipeline
- `orchestrator.py` - Workflow coordination and orchestration
- `enhanced_summarizer.py` - AI-powered code summarization

### Storage (storage/)
- `vector_store.py` - Vector database operations (Qdrant)
- `repo_state.py` - Repository processing state tracking

### Utilities (utils/)
- `rate_limiter.py` - API rate limiting and quota management
- `logging_config.py` - Structured logging configuration
- `summary_templates.py` - Code summary templates
- `change_planner.py` - Change analysis and planning

### Parsers (parsers/)
- Language-specific code parsers using Tree-sitter
- Support for Python, Java, Kotlin, Dart, JavaScript

### Examples (examples/)
- Usage examples and sample code

### Documentation (docs/)
- Architecture documentation
- API documentation
- Running instructions

### Tests (tests/)
- Unit and integration tests

## Quick Start

```python
from code_intelligence.core import CodeIntelligenceOrchestrator

# Initialize orchestrator
orchestrator = CodeIntelligenceOrchestrator(repo_path="/path/to/repo")

# Embed repository with GitHub LLM analysis
stats = await orchestrator.embed_repository(
    github_repository="owner/repo",
    query="authentication logic",
    collection_name="my_code"
)
```

## Module Exports
"""

from .core import (
    EmbeddingPipeline,
    CodeIntelligenceOrchestrator,
    EnhancedSummarizer,
)

from .storage import (
    VectorStore,
    EmbeddingPoint,
    RepoState,
)

from .utils import (
    RateLimiter,
    QuotaType,
    setup_logging,
    get_logger,
    SummaryTemplates,
    ChangePlanner,
)

__version__ = "1.0.0"

__all__ = [
    # Core
    "EmbeddingPipeline",
    "CodeIntelligenceOrchestrator",
    "EnhancedSummarizer",
    
    # Storage
    "VectorStore",
    "EmbeddingPoint",
    "RepoState",
    
    # Utils
    "RateLimiter",
    "QuotaType",
    "setup_logging",
    "get_logger",
    "SummaryTemplates",
    "ChangePlanner",
]
