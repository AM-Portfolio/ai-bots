# Vector Database Usage Guide

## Overview
The Vector Database system allows you to index GitHub repositories and perform semantic search over code and documentation.

## Quick Start

### 1. Check Vector DB Status
```bash
curl http://localhost:8000/api/vector-db/status
```

### 2. Get Repository Examples
```bash
curl http://localhost:8000/api/vector-db/examples
```

### 3. Index a Repository

**Small Repository (Recommended for testing):**
```bash
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "psf",
    "repo": "requests",
    "branch": "main",
    "collection": "github_repos"
  }'
```

**Medium Repository:**
```bash
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "facebook",
    "repo": "react",
    "branch": "main",
    "collection": "github_repos"
  }'
```

### 4. Perform Semantic Search
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to handle HTTP requests",
    "collection": "github_repos",
    "top_k": 5
  }'
```

### 5. Use GitHub-LLM Query (Intelligent Orchestration)
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "explain how authentication works",
    "query_type": "semantic_search",
    "max_results": 5
  }'
```

## API Endpoints

### `GET /api/vector-db/status`
Check Vector DB system status

### `GET /api/vector-db/examples`
Get example repositories for indexing

### `POST /api/vector-db/index-repository`
Index a GitHub repository
```json
{
  "owner": "facebook",      // Required: GitHub username or organization
  "repo": "react",          // Required: Repository name
  "branch": "main",         // Optional: Default is "main"
  "collection": "github_repos"  // Optional: Default is "github_repos"
}
```

### `POST /api/vector-db/semantic-search`
Perform semantic search
```json
{
  "query": "error handling patterns",  // Required: Search query
  "collection": "github_repos",        // Optional
  "top_k": 5,                          // Optional: Number of results
  "repository": "facebook/react",      // Optional: Filter by repo
  "language": "javascript"             // Optional: Filter by language
}
```

### `POST /api/vector-db/query`
Intelligent GitHub-LLM query with orchestration
```json
{
  "query": "how does routing work?",
  "query_type": "semantic_search",
  "repository": "facebook/react",
  "max_results": 5
}
```

## Features

### Supported File Types
- **Code**: .py, .js, .ts, .jsx, .tsx, .java, .go, .rs, .c, .cpp, .cs, .rb, .php, .swift
- **Documentation**: .md, .rst, .txt
- **Configuration**: .yaml, .yml, .json, .toml

### Intelligent Features
1. **Semantic Search**: Find code by meaning, not just keywords
2. **GitHub-LLM Orchestration**: Intelligent query planning and execution
3. **Response Beautification**: LLM-powered formatting for better readability
4. **Language Detection**: Automatic programming language identification
5. **Metadata Tracking**: Full provenance tracking (repo, file path, commit SHA)

## Tips

1. **Start Small**: Begin with repositories under 1,000 files
2. **Be Patient**: Large repositories may take 10+ minutes to index
3. **Branch Selection**: Use stable branches (main/master) for consistency
4. **Memory Limits**: Very large files (>500KB) are automatically skipped
5. **Rate Limits**: GitHub API has rate limits; indexing pauses if limits are reached

## Troubleshooting

### "404: Repository not found"
- Verify the owner and repo names are correct
- Ensure the repository is public
- Check that GITHUB_TOKEN has access to the repository

### "No documents to index"
- The repository may not have any supported file types
- Try a different branch (e.g., "master" instead of "main")

### "503: Vector DB not initialized"
- Restart the application
- Check logs for initialization errors

## Examples by Use Case

### Index Your Own Repository
```bash
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "YOUR_GITHUB_USERNAME",
    "repo": "YOUR_REPO_NAME",
    "branch": "main"
  }'
```

### Search Across Multiple Repositories
After indexing several repositories, search across all of them:
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication implementation",
    "top_k": 10
  }'
```

### Filter by Repository
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "hooks usage",
    "repository": "facebook/react",
    "top_k": 5
  }'
```

### Filter by Language
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "async await patterns",
    "language": "python",
    "top_k": 5
  }'
```
