# Code Intelligence - Quick Reference

## 🚀 Getting Started

```bash
# Run from root directory
cd code-intelligence

# Embed repository
python orchestrator.py embed

# With GitHub analysis
python orchestrator.py embed --github-repo owner/repo --query "feature"

# Health check
python orchestrator.py health
```

## 📁 Structure Overview

```
orchestrator.py          🎯 Main entry point
├── analysis/           📊 Analysis modules (GitHub, changes, health)
├── pipeline/           ⚙️  Workflows (embedding storage)
├── commands/           🖥️  CLI handlers
├── storage/            💾 Vector DB & state
├── utils/              🔧 Utilities
├── parsers/            📝 Language parsers
└── docs/               📚 Documentation
```

## 📖 Documentation

- **[REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md)** - Full structure guide
- **[ORGANIZATION.md](ORGANIZATION.md)** - Organization details
- **[docs/MODULAR_ARCHITECTURE.md](docs/MODULAR_ARCHITECTURE.md)** - Architecture guide

## 🎯 Key Files

- `orchestrator.py` - **START HERE** - Main CLI and coordinator
- `embed_repo.py` - Embedding generation pipeline
- `analysis/github_analyzer.py` - GitHub LLM analysis
- `pipeline/embedding_workflow.py` - Storage workflow
- `storage/vector_store.py` - Vector database operations

## 💡 Quick Examples

### CLI Usage
```bash
# Embed with GitHub filter
python orchestrator.py embed \
  --github-repo AM-Portfolio/ai-bots \
  --query "vector database" \
  --language python

# Analyze changes
python orchestrator.py analyze --base origin/main

# GitHub repo analysis
python orchestrator.py repo-analyze \
  --repository owner/repo \
  --query "authentication"
```

### Python API
```python
from code_intelligence import CodeIntelligenceOrchestrator

orchestrator = CodeIntelligenceOrchestrator(repo_path=".")
stats = await orchestrator.embed_repository(
    github_repository="owner/repo",
    query="auth logic"
)
```

## 🔧 Development

### Run Tests
```bash
python orchestrator.py test
```

### Add New Analyzer
1. Create `analysis/my_analyzer.py`
2. Add to `analysis/__init__.py`
3. Use in orchestrator

### Add New Command
1. Add handler to `commands/handlers.py`
2. Add CLI parser in `orchestrator.py`

---

**Status:** Production Ready ✅
