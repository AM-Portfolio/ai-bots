# Migration Guide: Repository Indexing → Code Intelligence

## Overview

The `RepositoryIndexer` from `shared.vector_db.services` has been **deprecated** and replaced by the more powerful **code-intelligence** module.

## Why Migrate?

### Old: `RepositoryIndexer` (Deprecated)
- ❌ Simple file-based indexing from GitHub API
- ❌ No semantic code parsing
- ❌ Basic text chunking
- ❌ No summarization
- ❌ Limited language support
- ❌ No change detection
- ❌ Basic rate limiting

### New: `Code Intelligence` (Recommended)
- ✅ Tree-sitter semantic parsing
- ✅ Enhanced summarization with technical + business context
- ✅ Multi-language support (Python, JS/TS, Java, Kotlin, C/C++, Dart)
- ✅ Incremental updates (only changed files)
- ✅ Smart prioritization (changed files first)
- ✅ Adaptive rate limiting with batching
- ✅ Special file detection (Docker, Helm, configs, API specs)
- ✅ Resilient error handling with DLQ
- ✅ Two-phase pipeline: summarize → embed
- ✅ Caching layer for performance

---

## Migration Steps

### Step 1: Remove Old Import

**Before:**
```python
from shared.vector_db.services.repository_indexer import RepositoryIndexer
```

**After:**
```python
# Option A: Use embedding orchestrator directly
from code_intelligence.embed_repo import EmbeddingOrchestrator

# Option B: Use unified orchestrator (recommended)
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator
```

### Step 2: Update Initialization

**Before:**
```python
indexer = RepositoryIndexer(
    vector_db=vector_db,
    embedding_service=embedding_service,
    github_client=github_client
)
```

**After (Option A - Direct):**
```python
orchestrator = EmbeddingOrchestrator(
    repo_path=".",  # Local repository path
    collection_name="code_intelligence"
)
```

**After (Option B - Unified):**
```python
orchestrator = CodeIntelligenceOrchestrator(
    repo_path="."  # Local repository path
)
```

### Step 3: Update Indexing Call

**Before:**
```python
result = await indexer.index_repository(
    owner="facebook",
    repo="react",
    branch="main",
    collection_name="github_repos"
)
```

**After (Option A):**
```python
stats = await orchestrator.run_incremental(
    max_files=None,  # No limit
    force_reindex=False  # Only changed files
)
```

**After (Option B):**
```python
stats = await orchestrator.embed_repository(
    collection_name="code_intelligence",
    max_files=None,
    force_reindex=False
)
```

### Step 4: Update Result Handling

**Before:**
```python
if result['success']:
    print(f"Indexed {result['documents_indexed']} documents")
```

**After:**
```python
print(f"Files processed: {stats['files_processed']}")
print(f"Chunks embedded: {stats['chunks_embedded']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

---

## Complete Examples

### Example 1: Basic Migration

**Old Code:**
```python
from shared.vector_db.services.repository_indexer import RepositoryIndexer
from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.embedding_service import EmbeddingService

async def index_repo():
    vector_db = VectorDBFactory.create_provider("qdrant")
    embedding_service = EmbeddingService()
    
    indexer = RepositoryIndexer(
        vector_db=vector_db,
        embedding_service=embedding_service
    )
    
    result = await indexer.index_repository(
        owner="myorg",
        repo="myrepo",
        branch="main"
    )
    
    return result
```

**New Code:**
```python
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator

async def index_repo():
    orchestrator = CodeIntelligenceOrchestrator(
        repo_path="."  # Or path to your local repo
    )
    
    stats = await orchestrator.embed_repository(
        collection_name="code_intelligence"
    )
    
    return stats
```

### Example 2: API Endpoint Migration

**Old Code:**
```python
@router.post("/index-repository")
async def index_repository(owner: str, repo: str, branch: str = "main"):
    indexer = RepositoryIndexer(
        vector_db=vector_db,
        embedding_service=embedding_service,
        github_client=github_client
    )
    
    result = await indexer.index_repository(
        owner=owner,
        repo=repo,
        branch=branch,
        collection_name="github_repos"
    )
    
    return result
```

**New Code:**
```python
@router.post("/index-repository")
async def index_repository(repo_path: str, collection: str = "code_intelligence"):
    import sys
    from pathlib import Path
    
    # Add code-intelligence to path
    code_intel_path = Path(__file__).parent.parent / "code-intelligence"
    sys.path.append(str(code_intel_path))
    
    from embed_repo import EmbeddingOrchestrator
    
    orchestrator = EmbeddingOrchestrator(
        repo_path=repo_path,
        collection_name=collection
    )
    
    stats = await orchestrator.run_incremental()
    
    return {
        'success': True,
        'statistics': stats
    }
```

### Example 3: Command-Line Usage

**Old:**
```bash
# No CLI available - had to write custom script
```

**New:**
```bash
# Use unified orchestrator CLI
python orchestrator.py embed --repo . --collection my_project

# With options
python orchestrator.py embed --max-files 100 --force

# Check health first
python orchestrator.py health

# Analyze changes
python orchestrator.py analyze
```

---

## Key Differences

| Feature | Old (RepositoryIndexer) | New (Code Intelligence) |
|---------|------------------------|-------------------------|
| **Input** | GitHub owner/repo/branch | Local repository path |
| **Parsing** | None (raw text) | Tree-sitter semantic parsing |
| **Chunking** | Fixed size | Function/class level |
| **Summarization** | None | Enhanced with templates |
| **Languages** | All (as text) | Python, JS/TS, Java, Kotlin, C/C++, Dart |
| **Change Detection** | No | SHA256 hashing |
| **Incremental** | No | Yes (default) |
| **Prioritization** | No | Yes (changed files first) |
| **Rate Limiting** | Basic | Adaptive batching |
| **Caching** | No | Summaries + embeddings |
| **Special Files** | No | Docker, Helm, configs, API specs |
| **Error Handling** | Basic | DLQ with retry |
| **CLI** | No | Yes (orchestrator.py) |

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Embedding Service
EMBEDDING_PROVIDER=azure  # or together
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_API_VERSION=2023-05-15
AZURE_OPENAI_EMBEDDING_BATCH_SIZE=20
AZURE_OPENAI_EMBEDDING_BATCH_DELAY=1.0

# LLM for Summarization
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Vector Database
QDRANT_URL=http://localhost:6333
# or
QDRANT_PATH=./qdrant_data
```

---

## Advanced Features

### 1. Incremental Updates (Default)
```python
# Only embeds changed files since last run
stats = await orchestrator.run_incremental()
```

### 2. Force Full Re-index
```python
# Re-embed everything
stats = await orchestrator.run_incremental(force_reindex=True)
```

### 3. Limit File Count
```python
# Process only first 50 files
stats = await orchestrator.run_incremental(max_files=50)
```

### 4. Custom Collection
```python
orchestrator = EmbeddingOrchestrator(
    repo_path=".",
    collection_name="my_custom_collection"
)
```

### 5. Health Checks
```python
orchestrator = CodeIntelligenceOrchestrator(repo_path=".")
health = await orchestrator.health_check()

if health['embedding_service']:
    print("✅ Ready to embed")
```

### 6. Change Analysis
```python
orchestrator = CodeIntelligenceOrchestrator(repo_path=".")
analysis = await orchestrator.analyze_changes()

print(f"Changed files: {analysis['changed_files']}")
```

---

## Troubleshooting

### "Module not found: embed_repo"

**Solution:**
```python
import sys
from pathlib import Path

code_intel_path = Path(__file__).parent.parent / "code-intelligence"
sys.path.append(str(code_intel_path))

from embed_repo import EmbeddingOrchestrator
```

### "Embedding service not connected"

**Solution:**
```bash
# Check health first
python orchestrator.py health

# Verify .env configuration
# Ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY are set
```

### "429 Too Many Requests"

**Solution:**
```bash
# Increase batch delay in .env
AZURE_OPENAI_EMBEDDING_BATCH_DELAY=2.0

# Or decrease batch size
AZURE_OPENAI_EMBEDDING_BATCH_SIZE=10
```

---

## Support

- **Documentation**: See `code-intelligence/README.md`
- **Quick Reference**: See `code-intelligence/QUICK_REFERENCE.md`
- **Integration Guide**: See `code-intelligence/INTEGRATION_GUIDE.md`
- **Features**: See `code-intelligence/ENHANCED_FEATURES.md`

---

## Timeline

- **Current**: `RepositoryIndexer` marked as deprecated
- **Next Release**: Remove `RepositoryIndexer` completely
- **Action Required**: Migrate to code-intelligence module now
