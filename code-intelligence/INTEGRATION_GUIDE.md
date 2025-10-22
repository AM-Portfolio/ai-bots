# Code Intelligence Integration Guide

## Overview

The Code Intelligence system is now **fully integrated** with the main application's vector database API!

This integration allows you to:
- ✅ Embed repositories with rich technical summaries via REST API
- ✅ Query code using semantic search with enhanced context
- ✅ Use the same Azure AI providers as the rest of the application
- ✅ Store embeddings in the main vector database (Qdrant)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Main Application (FastAPI)                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐      ┌─────────────────────────┐   │
│  │  Azure AI      │◄────►│  Code Intelligence API  │   │
│  │  Manager       │      │  /api/code-intelligence │   │
│  └────────────────┘      └──────────┬──────────────┘   │
│           ▲                          │                   │
│           │                          ▼                   │
│  ┌────────┴────────┐      ┌─────────────────────────┐   │
│  │  LLM Providers  │      │  Enhanced Summarizer    │   │
│  │  (Azure, etc.)  │      │  (50+ tech stacks)      │   │
│  └─────────────────┘      └──────────┬──────────────┘   │
│                                       │                   │
│                                       ▼                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Vector Database (Qdrant)               │    │
│  │  • Code chunks + enhanced summaries             │    │
│  │  • Technical metadata (imports, exceptions)     │    │
│  │  • Business context (purpose, logic)            │    │
│  │  • Configuration details (env vars, configs)    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. **POST /api/code-intelligence/embed**

Embed a repository with enhanced summaries.

**Request:**
```json
{
  "repo_path": ".",
  "max_files": 50,
  "force_reindex": false,
  "collection_name": "code_intelligence"
}
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "files_discovered": 120,
    "files_changed": 15,
    "files_processed": 50,
    "chunks_generated": 450,
    "chunks_embedded": 445,
    "chunks_failed": 5,
    "success_rate": 98.9
  },
  "message": "Successfully embedded 445 code chunks"
}
```

**What it does:**
1. Discovers code files in repository
2. Detects changed files (incremental updates)
3. Prioritizes important files (entry points, changed files)
4. Parses code into chunks (functions, classes)
5. Generates rich technical summaries (enhanced summarizer)
6. Embeds code + summary together
7. Stores in vector database with metadata

---

### 2. **POST /api/code-intelligence/query**

Query code using semantic search.

**Request:**
```json
{
  "query": "How does caching work in this application?",
  "limit": 10,
  "filters": {
    "language": "python"
  }
}
```

**Response:**
```json
{
  "success": true,
  "query": "How does caching work in this application?",
  "total_results": 5,
  "results": [
    {
      "chunk_id": "abc123",
      "file_path": "services/user_service.py",
      "content": "async def get_user(id):\n    # Check cache first...",
      "summary": "Purpose: User retrieval with two-tier caching...",
      "score": 0.92,
      "metadata": {
        "language": "python",
        "symbol_name": "get_user",
        "chunk_type": "function"
      }
    }
  ]
}
```

---

### 3. **GET /api/code-intelligence/status**

Get system status and statistics.

**Response:**
```json
{
  "status": "ready",
  "vector_db": {
    "collection_name": "code_intelligence",
    "total_points": 445,
    "vector_dimension": 3072
  },
  "repository": {
    "total_files": 120,
    "total_chunks": 445,
    "languages": ["python", "javascript", "java"]
  },
  "supported_languages": ["python", "javascript", "java", "kotlin", "..."],
  "supported_extensions": [".py", ".js", ".ts", ".java", "..."]
}
```

---

### 4. **GET /api/code-intelligence/health**

Health check endpoint.

**Response:**
```json
{
  "healthy": true,
  "azure_openai": true,
  "vector_db": true
}
```

---

## Integration Features

### ✅ Shared Azure AI Resources

The code intelligence system uses the **same Azure AI Manager** as the main application:

```python
from shared.azure_services.azure_ai_manager import azure_ai_manager

# Code intelligence automatically uses:
# - Azure OpenAI for embeddings (text-embedding-3-large)
# - Azure OpenAI for summaries (GPT-4 mini)
# - Automatic fallback to Together AI if Azure is unavailable
```

**Benefits:**
- No duplicate API clients
- Consistent provider configuration
- Automatic fallback handling
- Shared rate limiting

---

### ✅ Integrated Vector Database

Code embeddings are stored in the **main Qdrant instance**:

```python
from shared.vector_db.embedding_service import EmbeddingService

# Uses the same vector DB as:
# - Document embeddings
# - Chat history embeddings
# - Analysis results
```

**Benefits:**
- Single vector database instance
- Unified querying across all embeddings
- Consistent metadata structure
- Shared persistence

---

### ✅ Enhanced Summarization

Code chunks are enriched with **comprehensive technical summaries**:

```python
# Before: "Function get_user in UserService"
# After:
"""
Purpose: User retrieval with caching and database fallback
Technical: FastAPI async + Redis + PostgreSQL
Business Logic: Handles user profile access with cache optimization
Configuration: DATABASE_URL, REDIS_URL, CACHE_TTL
Error Handling: HTTP 404 (not found), 503 (database unavailable)
Performance: 90% cache hit rate, <50ms average response time
API: async get_user(user_id: int) -> User | HTTPException
"""
```

---

## Usage Examples

### Example 1: Embed Your Repository

```bash
# Via API
curl -X POST http://localhost:5000/api/code-intelligence/embed \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": ".",
    "max_files": 50
  }'

# Or via Python
import requests

response = requests.post(
    "http://localhost:5000/api/code-intelligence/embed",
    json={
        "repo_path": ".",
        "max_files": 50,
        "force_reindex": False
    }
)

print(response.json())
```

---

### Example 2: Query Code

```bash
# Via API
curl -X POST http://localhost:5000/api/code-intelligence/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do we handle database connection failures?",
    "limit": 10
  }'

# Or via Python
response = requests.post(
    "http://localhost:5000/api/code-intelligence/query",
    json={
        "query": "How do we handle database connection failures?",
        "limit": 10,
        "filters": {
            "language": "python"
        }
    }
)

for result in response.json()["results"]:
    print(f"File: {result['file_path']}")
    print(f"Score: {result['score']}")
    print(f"Summary: {result['summary']}")
    print("---")
```

---

### Example 3: Cross-Stack Search

```python
# Find all code using Redis
response = requests.post(
    "http://localhost:5000/api/code-intelligence/query",
    json={
        "query": "Redis caching implementation",
        "limit": 20
    }
)

# Results include:
# - Python code using Redis
# - Docker Compose with Redis service
# - Config files with REDIS_URL
# - Infrastructure code provisioning ElastiCache
```

---

## Advanced Queries

### Query by Technology

```python
queries = [
    "Kafka topic configuration",
    "PostgreSQL database migrations",
    "Terraform AWS infrastructure",
    "GitHub Actions CI/CD pipeline",
    "Prometheus monitoring alerts"
]

for query in queries:
    results = requests.post(
        "http://localhost:5000/api/code-intelligence/query",
        json={"query": query, "limit": 5}
    ).json()
    
    print(f"\n🔍 {query}")
    for r in results["results"]:
        print(f"  • {r['file_path']} (score: {r['score']:.2f})")
```

---

### Query by Business Logic

```python
# Find authentication logic
results = requests.post(
    "http://localhost:5000/api/code-intelligence/query",
    json={
        "query": "user authentication and session management",
        "limit": 10
    }
).json()

# Results include:
# - Login endpoints
# - Session validation
# - JWT token handling
# - Password hashing
```

---

### Query by Configuration

```python
# Find all code using specific env vars
results = requests.post(
    "http://localhost:5000/api/code-intelligence/query",
    json={
        "query": "API_KEY environment variable usage",
        "limit": 10
    }
).json()

# Results include:
# - .env files
# - Docker Compose configs
# - Terraform variables
# - Python code reading API_KEY
```

---

## Rate Limiting & Performance

### Automatic Rate Limiting

The system handles Azure OpenAI rate limits automatically:

```python
# Adaptive batching: 1-16 chunks per request
# Exponential backoff on 429 errors
# Automatic retry with intelligent queueing

# Example throughput:
# - Small repo (50 files, 200 chunks): ~5 minutes
# - Medium repo (200 files, 1000 chunks): ~20 minutes
# - Large repo (500 files, 3000 chunks): ~60 minutes
```

### Incremental Updates

Only changed files are re-embedded:

```python
# First run: 100 files, 500 chunks embedded
# Second run: 5 files changed, only 25 chunks re-embedded
# 95% cache hit rate!

# Force full reindex:
requests.post(
    "http://localhost:5000/api/code-intelligence/embed",
    json={"force_reindex": True}
)
```

---

## Monitoring & Observability

### Check System Status

```bash
curl http://localhost:5000/api/code-intelligence/status
```

Returns:
- Vector DB statistics
- Repository statistics
- Supported languages
- Collection info

### Health Check

```bash
curl http://localhost:5000/api/code-intelligence/health
```

Returns:
- System health
- Azure OpenAI availability
- Vector DB connectivity

---

## Error Handling

The system handles errors gracefully:

```python
# API errors return structured responses:
{
    "detail": "Azure OpenAI not configured",
    "status_code": 500
}

# Failed chunks go to DLQ for retry:
# - Logged for investigation
# - Retried with exponential backoff
# - Skipped if persistently failing
```

---

## Best Practices

### 1. Start Small
```python
# First embedding: limit files
requests.post(
    "http://localhost:5000/api/code-intelligence/embed",
    json={"max_files": 20}
)
```

### 2. Use Incremental Updates
```python
# Regular updates: only changed files
requests.post(
    "http://localhost:5000/api/code-intelligence/embed",
    json={"force_reindex": False}  # default
)
```

### 3. Filter Queries
```python
# Use filters for faster searches
requests.post(
    "http://localhost:5000/api/code-intelligence/query",
    json={
        "query": "authentication logic",
        "filters": {
            "language": "python",
            "chunk_type": "function"
        }
    }
)
```

---

## Next Steps

1. **Embed your repository:**
   ```bash
   curl -X POST http://localhost:5000/api/code-intelligence/embed \
     -H "Content-Type: application/json" \
     -d '{"repo_path": ".", "max_files": 50}'
   ```

2. **Query your code:**
   ```bash
   curl -X POST http://localhost:5000/api/code-intelligence/query \
     -H "Content-Type: application/json" \
     -d '{"query": "How does caching work?", "limit": 10}'
   ```

3. **Check status:**
   ```bash
   curl http://localhost:5000/api/code-intelligence/status
   ```

---

## Summary

✅ **Fully Integrated** with main application  
✅ **Shared Azure AI** providers and rate limiting  
✅ **Enhanced Summaries** with 50+ tech stack support  
✅ **REST API** for embedding and querying  
✅ **Incremental Updates** for efficiency  
✅ **Production Ready** with error handling and monitoring  

**Your code intelligence system is now accessible via REST API!** 🚀
