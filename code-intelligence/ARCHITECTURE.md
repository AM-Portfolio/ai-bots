# Code Intelligence - Architecture Overview

## Structure

The code-intelligence module is now cleanly separated into:

### Core Orchestration
- **`orchestrator.py`** - Core orchestration logic (library)
  - `CodeIntelligenceOrchestrator` class
  - High-level workflows for embedding, summarization, analysis
  - No CLI code - pure business logic
  - Designed to be imported by APIs and CLI

### CLI Layer
- **`main.py`** - CLI entry point
  - Argument parsing
  - Command routing
  - Logging configuration
  - Calls command handlers

- **`commands/`** - Command handlers
  - `cmd_embed.py` - Embedding command
  - `cmd_summarize.py` - Summarization command
  - `cmd_analyze.py` - Git-based change analysis
  - `cmd_repo_analyze.py` - GitHub LLM analysis
  - `cmd_health.py` - Health check
  - `cmd_test.py` - Integration tests

### Pipeline Modules
- **`embed_repo.py`** - Embedding pipeline (no CLI)
- **`enhanced_summarizer.py`** - Code summarization orchestrator
- **`pipeline/`** - Specialized pipeline components
  - `file_discovery.py` - File discovery and filtering
  - `code_parser.py` - Code parsing and chunking
  - `batch_embedder.py` - Batch embedding generation
  - `embedding_workflow.py` - Storage workflow

### Analysis
- **`analysis/`**
  - `github_analyzer.py` - GitHub LLM integration

### Utilities
- **`utils/`**
  - `metadata_extractor.py` - Extract code metadata
  - `file_type_detector.py` - Detect file types
  - `prompt_builder.py` - Build prompts
  - `fallback_summarizer.py` - Fallback summaries
  - `summary_batcher.py` - Batch processing
  - `rate_limiter.py` - Rate limiting
  - `change_planner.py` - Change prioritization
  - `logging_config.py` - Logging setup

### Storage
- **`storage/`**
  - `vector_store.py` - Vector database interface
  - `repo_state.py` - Repository state tracking

## Usage

### Command Line
```bash
# Run from repository root
python code-intelligence/main.py embed
python code-intelligence/main.py embed --force --max-files 50
python code-intelligence/main.py repo-analyze --repository owner/repo
python code-intelligence/main.py health
```

### Python API
```python
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator

# Create orchestrator
orchestrator = CodeIntelligenceOrchestrator(repo_path=".")

# Embed repository
stats = await orchestrator.embed_repository(
    collection_name="my_code",
    max_files=100,
    force_reindex=False
)

# Health check
health = await orchestrator.health_check()

# Analyze changes
results = await orchestrator.analyze_changes(base_ref="origin/main")
```

### Direct Analyzer Usage
```python
from code_intelligence.analysis.github_analyzer import GitHubAnalyzer

# Use GitHub LLM directly
analyzer = GitHubAnalyzer()
result = await analyzer.analyze_repository(
    repository="owner/repo",
    query="vector database",
    max_results=10
)
```

## Design Principles

1. **Separation of Concerns**
   - Orchestrator = business logic only
   - Commands = CLI interface only
   - No mixing of concerns

2. **Single Responsibility**
   - Each module has one clear purpose
   - Small, focused classes
   - Easy to test and maintain

3. **API First**
   - Orchestrator designed for programmatic use
   - CLI is just one consumer
   - Easy to integrate with web APIs

4. **Modularity**
   - Extract specialized modules for each concern
   - Reusable components
   - Clear dependencies

## Migration Notes

### Before
```bash
python code-intelligence/orchestrator.py embed
```

### After
```bash
python code-intelligence/main.py embed
```

The `orchestrator.py` is now a library module - import it, don't run it directly.
Use `main.py` for CLI operations.
