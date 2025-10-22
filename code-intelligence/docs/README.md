# Code Intelligence Embedding Pipeline

Optimized multi-language code embedding system with intelligent rate limiting, caching, and incremental updates.

## 🎯 Features

- **Enhanced Summarization** ⭐ NEW: Rich, structured summaries with technical details, business logic, configurations, error handling, API specs, and performance notes
- **Comprehensive Logging** ⭐ NEW: 4 log levels (quiet/normal/verbose/debug) with detailed progress tracking and file logging
- **Smart Filtering** ⭐ NEW: Automatically excludes node_modules, tests, build outputs (60-80% reduction)
- **Multi-Language Support**: Python, JavaScript/TypeScript, Java, Kotlin, C/C++, Dart (Flutter), and more
- **Intelligent Rate Limiting**: Adaptive batching with exponential backoff to prevent Azure 429 errors
- **Incremental Updates**: Only embeds changed files using SHA256 hashing
- **Smart Prioritization**: Changed files and entry points processed first
- **Two-Phase Pipeline**: Summarization → Embedding for optimal quality
- **Special File Detection**: Auto-detects Docker, Helm, API specs, configs, and applies specialized analysis
- **Caching**: Summaries and embeddings cached to avoid reprocessing
- **Tree-Sitter Parsing**: Semantic chunking at function/class level
- **Resilient**: DLQ for failed chunks, automatic retry with backoff
- **Production Ready**: Scales to 10K+ files with efficient filtering and logging

## 📂 Architecture

```
code-intelligence/
├── orchestrator.py            # ⭐ MAIN ENTRY POINT - Unified command interface
├── embed_repo.py              # Embedding pipeline orchestrator
├── enhanced_summarizer.py     # Rich technical summaries
├── summary_templates.py       # Summary prompt templates
├── logging_config.py          # ⭐ NEW: Logging configuration system
├── change_planner.py          # Smart file prioritization
├── repo_state.py              # File hashing & caching
├── rate_limiter.py            # Azure-aware rate limiting
├── vector_store.py            # Qdrant interface
├── test_pipeline.py           # Integration tests
├── LOGGING_IMPROVEMENTS.md    # ⭐ NEW: Detailed logging guide
├── LOGGING_QUICK_REF.md       # ⭐ NEW: Quick logging reference
├── examples/                  # Sample code & docs
└── parsers/
    ├── __init__.py        # Parser registry
    ├── base_parser.py     # Base interface
    ├── python_parser.py   # Python (tree-sitter)
    ├── js_parser.py       # JavaScript/TypeScript
    ├── java_parser.py     # Java
    ├── cpp_parser.py      # C/C++
    ├── kotlin_parser.py   # Kotlin
    ├── dart_parser.py     # Dart (Flutter)
    └── fallback_parser.py # Generic fallback
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure OpenAI

```bash
# Copy example config
cp .env.example .env

# Edit .env with your Azure credentials
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_KEY=your-api-key
```

### 3. Run Code Intelligence

**NEW: Use the unified orchestrator.py entry point for all operations**

```bash
# Check system health
python orchestrator.py health

# Embed repository (incremental - only changed files)
python orchestrator.py embed

# Force re-embed all files
python orchestrator.py embed --force

# With verbose logging to see API calls
python orchestrator.py embed --log-level verbose

# Debug mode with file logging
python orchestrator.py embed --log-level debug --log-file debug.log

# Production mode (quiet)
python orchestrator.py embed --log-level quiet

# Limit to 50 files
python orchestrator.py embed --max-files 50

# Custom collection name
python orchestrator.py embed --collection my_project

# Analyze repository changes and priorities
python orchestrator.py analyze

# Generate code summaries
python orchestrator.py summarize

# Run integration tests
python orchestrator.py test
```

**See [LOGGING_QUICK_REF.md](LOGGING_QUICK_REF.md) for logging guide**

**Legacy: Direct script execution (still supported)**

```bash
# Direct embedding (legacy approach)
python embed_repo.py --repo . --collection my_project
```

## 🔧 How It Works

### Flow Diagram

```
Git Repo → Discover Files → Detect Changes → Prioritize
    ↓
Parse with tree-sitter → Code Chunks (200-400 tokens)
    ↓
Phase 1: GPT-4 mini summaries (cached) → Rate Limiter
    ↓
Phase 2: Embed (code + summary) → Rate Limiter
    ↓
Store in Qdrant → Update manifest
```

### Key Components

**1. Rate Limiter**
- Tracks requests per minute (RPM) and tokens per minute (TPM)
- Adaptive batch sizing (1-16 chunks)
- Exponential backoff on 429 errors
- Separate quotas for embeddings vs summaries

**2. Repo State**
- SHA256 hashing for change detection
- Caches summaries to avoid re-generation
- Tracks embedding IDs for each chunk
- Fast incremental updates

**3. Change Planner**
- Priority 0: Changed entry points
- Priority 1: Changed core files (high imports)
- Priority 2: Changed regular files
- Priority 3+: Unchanged files by importance

**4. Parser Registry**
- Automatically selects parser by file extension
- Tree-sitter for semantic chunking
- Fallback to line-based chunking
- Target chunk size: 200-400 tokens

**5. Summarizer**
- Azure GPT-4 mini for concise summaries
- Caches summaries by chunk hash
- Structured prompts optimized for code
- Fallback to simple summaries on error

**6. Vector Store**
- Qdrant with Cosine similarity
- Bulk upsert with retry logic
- Rich metadata schema
- Health verification

## 📊 Solving Rate Limits

The pipeline handles Azure rate limits intelligently:

### Before (❌ Rate Limited)
```
Processing 190 chunks sequentially...
Chunk 10/190: HTTP 429 - Wait 48 seconds
Chunk 11/190: HTTP 429 - Wait 60 seconds
Total time: 2+ hours with frequent failures
```

### After (✅ Optimized)
```
Processing 190 chunks in adaptive batches...
Batch 1 (16 chunks): Success
Batch 2 (16 chunks): Success
Batch 3 (8 chunks): 429 detected, reducing batch size
Batch 4 (4 chunks): Success with backoff
Total time: 15-20 minutes with high success rate
```

## 🎛️ Configuration

### Rate Limits (rate_limiter.py)

```python
RateLimitConfig(
    requests_per_minute=60,      # API requests/min
    tokens_per_minute=90000,     # Token limit/min
    max_batch_size=16,           # Max chunks per batch
    min_batch_size=1,            # Min chunks per batch
    initial_retry_delay=1.0,     # Initial backoff (seconds)
    max_retry_delay=60.0         # Max backoff (seconds)
)
```

### Chunking (parsers/base_parser.py)

```python
BaseParser(
    target_chunk_tokens=300,     # Target chunk size
    max_chunk_tokens=400         # Maximum chunk size
)
```

## 📈 Monitoring

The pipeline provides detailed metrics:

```python
{
    "files_discovered": 150,
    "files_changed": 25,
    "files_processed": 25,
    "chunks_generated": 190,
    "chunks_embedded": 188,
    "chunks_failed": 2,
    "success_rate": 98.9,
    "rate_limiter_stats": {
        "embedding": {
            "total_requests": 12,
            "successful_requests": 12,
            "throttled_requests": 2,
            "success_rate": 100.0,
            "avg_response_time": 1.2
        }
    }
}
```

## 🔍 Query the Vector DB

```python
from code_intelligence.vector_store import VectorStore

store = VectorStore(collection_name="code_intelligence")

# Generate query embedding
query_text = "How does authentication work?"
query_embedding = # ... generate embedding

# Search
results = store.search(
    query_embedding=query_embedding,
    limit=10,
    score_threshold=0.7
)

for result in results:
    print(f"Score: {result['score']:.2f}")
    print(f"File: {result['metadata']['file_path']}")
    print(f"Summary: {result['summary']}")
    print(f"Code:\n{result['content'][:200]}...")
```

## 🛠️ Advanced Usage

### Custom Parsers

Add a new language by implementing `BaseParser`:

```python
from parsers.base_parser import BaseParser, CodeChunk

class GoParser(BaseParser):
    def get_language(self) -> str:
        return "go"
    
    def get_file_extension(self) -> List[str]:
        return ['.go']
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        # Implement parsing logic
        pass
```

Register in `parsers/__init__.py`:

```python
from .go_parser import GoParser
self.register('go', GoParser())
```

## 🐛 Troubleshooting

### Issue: Still getting 429 errors

**Solution**: Reduce batch size or increase retry delays

```python
# In rate_limiter.py
RateLimitConfig(
    max_batch_size=8,           # Smaller batches
    initial_retry_delay=2.0     # Longer backoff
)
```

### Issue: Embeddings taking too long

**Solution**: Increase batch size (if not rate limited)

```python
RateLimitConfig(
    max_batch_size=32,          # Larger batches
    requests_per_minute=120     # If you have higher quota
)
```

### Issue: Poor code chunk quality

**Solution**: Adjust chunk sizes

```python
BaseParser(
    target_chunk_tokens=200,    # Smaller chunks
    max_chunk_tokens=300
)
```

## 📝 State Management

The pipeline maintains state in `.code-intelligence-state.json`:

```json
{
  "version": "1.0",
  "files": {
    "src/main.py": {
      "sha256": "abc123...",
      "mtime": 1729622400.0,
      "chunk_count": 5,
      "status": "completed",
      "last_embedded": "2025-10-22T10:00:00"
    }
  },
  "chunks": {
    "main.py:chunk_0": {
      "chunk_hash": "def456...",
      "summary": "Main entry point function...",
      "embedding_id": "uuid-123",
      "status": "completed"
    }
  }
}
```

## 🎯 Best Practices

1. **Run incrementally**: Only re-embed on code changes
2. **Monitor rate limits**: Check `rate_limiter_stats` in output
3. **Adjust batch sizes**: Start small (4-8), increase if stable
4. **Cache summaries**: Keep manifest file in version control
5. **Test on subset**: Use `--max-files 10` for testing
6. **Review priorities**: Check which files are processed first

## 📚 Next Steps

- Add more language parsers (Go, Rust, Swift, etc.)
- Implement query router for semantic search
- Add dependency graph analysis
- Create visualization dashboard
- Integrate with CI/CD pipeline
