# Enhanced Query - Code Intelligence Search

## Overview

The enhanced query feature provides rich, structured search results from your embedded code repositories with proper formatting, relevance scoring, and metadata.

## Features

✨ **Smart Relevance Scoring**
- Excellent (90%+)
- Very Good (80-90%)
- Good (70-80%)
- Fair (60-70%)
- Configurable threshold filtering

📊 **Rich Result Formatting**
- File paths and line numbers
- Code syntax highlighting
- Relevance scores and rankings
- Metadata (imports, functions, classes)

🔍 **Intelligent Search**
- Natural language queries
- Code-specific searches
- Multi-file aggregation
- Language-aware results

## Usage

### Command Line

```bash
# Basic query
python code-intelligence/main.py query "vector database integration"

# Query specific repository
python code-intelligence/main.py query "authentication flow" --collection my-app

# Adjust results and threshold
python code-intelligence/main.py query "error handling" --limit 10 --threshold 0.8

# More lenient threshold for broader results
python code-intelligence/main.py query "logging" --threshold 0.6
```

### Python API

```python
from code_intelligence.utils.enhanced_query import EnhancedQueryService

# Initialize query service
query_service = EnhancedQueryService(collection_name="my_repo")

# Search for code
results = await query_service.search(
    query_text="how to handle authentication",
    limit=5,
    score_threshold=0.7
)

# Process results
for result in results["results"]:
    print(f"File: {result['file_path']}")
    print(f"Score: {result['score']} ({result['relevance']})")
    print(f"Code: {result['code']}")
    print(f"Functions: {result['metadata']['functions']}")
```

### Via Orchestrator

```python
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator

orchestrator = CodeIntelligenceOrchestrator()

# Query with orchestrator
results = await orchestrator.query(
    query_text="database connection pooling",
    collection_name="my_project",
    limit=5,
    score_threshold=0.7
)
```

## Response Format

```json
{
  "success": true,
  "query": "vector database integration",
  "collection": "code_intelligence",
  "summary": "Found 5 relevant code chunks across 3 file(s) in python language(s). Best match: vector_db/client.py (lines 45-78, score: 0.9234)",
  "results_count": 5,
  "results": [
    {
      "rank": 1,
      "score": 0.9234,
      "relevance": "Excellent",
      "file_path": "vector_db/client.py",
      "chunk_index": 2,
      "start_line": 45,
      "end_line": 78,
      "language": "python",
      "code": "class VectorDBClient:\n    def __init__(self, url: str):\n        ...",
      "metadata": {
        "repo_path": "/project/src",
        "file_type": "module",
        "imports": ["qdrant_client", "typing"],
        "functions": ["__init__", "connect", "search"],
        "classes": ["VectorDBClient"]
      }
    }
  ],
  "search_metadata": {
    "total_searched": 10,
    "threshold_applied": 0.7,
    "best_score": 0.9234,
    "average_score": 0.8456
  }
}
```

## Use Cases

### 1. Find Similar Code
```bash
python main.py query "error handling with try-except" --collection my-app
```

### 2. Locate Functionality
```bash
python main.py query "authentication middleware" --limit 10
```

### 3. Discover Patterns
```bash
python main.py query "database transaction patterns" --threshold 0.8
```

### 4. Code Documentation
```bash
python main.py query "API endpoint definitions" --collection backend
```

### 5. Cross-Repository Search
```bash
# Search different repositories
python main.py query "logging setup" --collection project-a
python main.py query "logging setup" --collection project-b
```

## Configuration

### Score Threshold

- **0.9+**: Exact or near-exact matches
- **0.8-0.9**: Very relevant results
- **0.7-0.8**: Good matches (default)
- **0.6-0.7**: Broader matches
- **<0.6**: May include less relevant results

### Result Limit

- Default: 5 results
- Recommended: 5-10 for focused search
- Maximum: Adjust based on needs

### Collection Names

Use meaningful collection names to organize different repositories:
- `backend-api` - Backend API code
- `frontend-react` - React frontend
- `shared-utils` - Shared utilities
- `infrastructure` - IaC and deployment

## Tips

1. **Use Natural Language**: "How to connect to database" works better than just "database"
2. **Be Specific**: More specific queries yield better results
3. **Adjust Threshold**: Lower threshold for exploratory searches
4. **Check Multiple Collections**: Search across different repos for patterns
5. **Review Metadata**: Use function/class names for context

## Integration

The enhanced query service is fully integrated with:
- ✅ Main CLI (`main.py query`)
- ✅ Orchestrator API (`orchestrator.query()`)
- ✅ Direct service (`EnhancedQueryService`)
- ✅ HTTP API endpoints (when deployed)

## Architecture

```
EnhancedQueryService
├── Embedding Generation (semantic search)
├── Vector Store Search (similarity matching)
├── Score Filtering (threshold-based)
├── Result Formatting (rich metadata)
└── Summary Generation (human-readable)
```
