# Code Intelligence Module - Quick Reference

## 🎯 Entry Point

**Use `orchestrator.py` as the single entry point for all operations.**

## 📋 Available Commands

### 1. Health Check
Check connectivity to all services (embedding, vector store, LLM)

```bash
python orchestrator.py health
```

**Output:**
```
🏥 Health Check Results:
✅ Overall Status: Healthy
  ✅ Embedding Service: OK
  ✅ Vector Store: OK
  ✅ LLM Service: OK
```

---

### 2. Embed Repository
Embed code into vector database for semantic search

```bash
# Incremental (only changed files)
python orchestrator.py embed

# Force re-embed everything
python orchestrator.py embed --force

# Limit number of files
python orchestrator.py embed --max-files 50

# Custom collection name
python orchestrator.py embed --collection my_project

# All options combined
python orchestrator.py embed --repo ../my-repo --collection my_project --max-files 100 --force
```

**Output:**
```
📊 Embedding Statistics:
  Files processed:  45
  Chunks embedded:  234
  Success rate:     98.5%
  Failed chunks:    3
```

---

### 3. Analyze Changes
Analyze git changes and file priorities

```bash
# Analyze current changes
python orchestrator.py analyze

# Compare against specific branch
python orchestrator.py analyze --base origin/main

# Skip priority display
python orchestrator.py analyze --no-display
```

**Output:**
```
📊 File Priorities:
Priority 0 (3 files):
  🔴 Changed 📍 Entry main.py
    Reason: Changed entry point

Priority 1 (5 files):
  🔴 Changed shared/config.py
    Reason: Changed core module
```

---

### 4. Generate Summaries
Generate enhanced code summaries with technical and business context

```bash
# Summarize all files
python orchestrator.py summarize

# Summarize specific files
python orchestrator.py summarize --files src/main.py src/utils.py

# Force regenerate cached summaries
python orchestrator.py summarize --force
```

**Output:**
```
📝 Summary Results:
  Files processed:      23
  Summaries generated:  18
  Cached summaries:     5
```

---

### 5. Run Tests
Execute integration tests

```bash
python orchestrator.py test
```

---

## 📚 Module Structure

### Core Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `orchestrator.py` | **Main entry point** | Always start here |
| `embed_repo.py` | Embedding pipeline | Called by orchestrator |
| `enhanced_summarizer.py` | Code summarization | Called by orchestrator |
| `change_planner.py` | Priority calculation | Called by orchestrator |
| `vector_store.py` | Qdrant interface | Storage operations |
| `repo_state.py` | File change tracking | Caching layer |
| `rate_limiter.py` | API rate limiting | Prevents 429 errors |
| `summary_templates.py` | Summary prompts | Template definitions |

### Support Files

| Directory/File | Purpose |
|----------------|---------|
| `parsers/` | Language-specific code parsers |
| `examples/` | Sample code and documentation |
| `test_pipeline.py` | Integration testing |
| `.env.example` | Configuration template |

---

## 🔧 Configuration

All configuration is in `.env` file (copy from `.env.example`):

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
# or use local storage
QDRANT_PATH=./qdrant_data

# Rate Limiting
AZURE_OPENAI_EMBEDDING_BATCH_SIZE=20
AZURE_OPENAI_EMBEDDING_BATCH_DELAY=1.0
```

---

## 🚦 Workflow Examples

### First-Time Setup
```bash
# 1. Check health
python orchestrator.py health

# 2. Embed repository
python orchestrator.py embed

# 3. Verify success
python orchestrator.py analyze
```

### Daily Development
```bash
# 1. Analyze what changed
python orchestrator.py analyze

# 2. Embed only changes (incremental)
python orchestrator.py embed

# 3. Generate new summaries
python orchestrator.py summarize --force
```

### Production Deployment
```bash
# Full re-index with all files
python orchestrator.py embed --force --collection production

# Verify health
python orchestrator.py health

# Run tests
python orchestrator.py test
```

---

## 💡 Tips

1. **Always run health check first** to verify connectivity
2. **Use incremental embedding** for faster updates (default behavior)
3. **Force re-embedding** only when schema changes or major updates
4. **Analyze changes** before embedding to see what will be processed
5. **Custom collections** for different projects or environments

---

## 🐛 Troubleshooting

### "Embedding service not connected"
```bash
# Check health
python orchestrator.py health

# Verify .env configuration
# Check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY
```

### "429 Too Many Requests"
```bash
# Increase batch delay in .env
AZURE_OPENAI_EMBEDDING_BATCH_DELAY=2.0

# Decrease batch size
AZURE_OPENAI_EMBEDDING_BATCH_SIZE=10
```

### "Qdrant connection failed"
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Or check local path exists
ls ./qdrant_data
```

---

## 📖 Further Documentation

- **README.md** - Comprehensive guide with architecture details
- **INTEGRATION_GUIDE.md** - Integration with other systems
- **QUICK_START.md** - Getting started guide
- **ENHANCED_FEATURES.md** - Advanced features and capabilities
- **TECH_STACK_SUPPORT.md** - Supported languages and frameworks
