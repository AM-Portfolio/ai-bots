# Vector Database & GitHub-LLM Integration Guide

## Overview
This system provides intelligent semantic search over your GitHub repositories using vector embeddings and LLM-powered response generation. It automatically detects GitHub-related queries and routes them through a specialized orchestration pipeline.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Indexing Repositories](#indexing-repositories)
3. [Querying the Vector Database](#querying-the-vector-database)
4. [Supported Query Types](#supported-query-types)
5. [Use Cases & Examples](#use-cases--examples)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Index a Repository
```bash
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "AM-Portfolio",
    "repo": "ai-bots",
    "branch": "feature/bot-testing",
    "collection": "github_repos"
  }'
```

**Response:**
```json
{
  "success": true,
  "repository": "AM-Portfolio/ai-bots",
  "branch": "feature/bot-testing",
  "documents_indexed": 147,
  "collection": "github_repos"
}
```

### Step 2: Check Indexing Status
```bash
curl http://localhost:8000/api/vector-db/status
```

**Response:**
```json
{
  "status": "healthy",
  "provider": "in-memory",
  "collections": {
    "github_repos": {
      "documents": 147,
      "dimension": 768
    }
  }
}
```

### Step 3: Query the Repository
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the API implementation",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "code_search",
    "top_k": 5
  }'
```

---

## Indexing Repositories

### API Endpoint
`POST /api/vector-db/index-repository`

### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `owner` | string | Yes | GitHub repository owner |
| `repo` | string | Yes | Repository name |
| `branch` | string | No | Branch name (default: main) |
| `collection` | string | No | Collection name (default: github_repos) |

### Example: Index Multiple Repositories
```bash
# Index your main project
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{"owner": "AM-Portfolio", "repo": "ai-bots", "branch": "main"}'

# Index a dependency library
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{"owner": "psf", "repo": "requests", "branch": "main"}'
```

### What Gets Indexed
- All code files (.py, .js, .ts, .java, .go, etc.)
- Documentation files (.md, .rst, .txt)
- Configuration files (.json, .yaml, .toml)
- Maximum file size: 100KB per file
- Binary files are excluded

### Indexing Time
- Small repos (< 50 files): ~30 seconds
- Medium repos (50-200 files): 2-3 minutes
- Large repos (200-500 files): 5-10 minutes

---

## Querying the Vector Database

### Method 1: Direct Semantic Search
**No LLM processing, just vector search results**

```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication implementation",
    "collection": "github_repos",
    "top_k": 5,
    "repository": "AM-Portfolio/ai-bots"
  }'
```

**Response:**
```json
{
  "query": "authentication implementation",
  "results": [
    {
      "content": "class AuthService...",
      "metadata": {
        "repo_name": "AM-Portfolio/ai-bots",
        "file_path": "shared/services/auth_service.py",
        "language": "python"
      },
      "score": 0.8542
    }
  ],
  "count": 5
}
```

### Method 2: GitHub-LLM Orchestrator
**Intelligent query processing with LLM-generated responses**

```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does authentication work in this codebase?",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "semantic_search",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "query": "How does authentication work in this codebase?",
  "response": "Based on the code analysis, the authentication system uses...",
  "sources": [
    {
      "file_path": "shared/services/auth_service.py",
      "content": "...",
      "score": 0.8542
    }
  ],
  "confidence": 0.85,
  "metadata": {
    "query_type": "semantic_search",
    "sources_used": 5
  }
}
```

### Method 3: LLM Testing UI (Automatic Detection)
Just ask naturally in the LLM Testing UI:

**Queries that trigger GitHub-LLM routing:**
- "Show me the API implementation"
- "Explain how authentication works in repo AM-Portfolio/ai-bots"
- "What does the UserService class do?"
- "Find code related to payment processing"
- "How do I use the GitHub API in this project?"

---

## Supported Query Types

### 1. Semantic Search
**Use Case:** Find conceptually related code/docs
```json
{
  "query_type": "semantic_search",
  "query": "database connection pooling"
}
```

**Best For:**
- Finding relevant code snippets
- Discovering related functionality
- Understanding system architecture

---

### 2. Code Search
**Use Case:** Search for specific code patterns
```json
{
  "query_type": "code_search",
  "query": "async function that handles HTTP requests"
}
```

**Best For:**
- Finding specific implementations
- Locating API endpoints
- Discovering utility functions

---

### 3. File Explanation
**Use Case:** Understand what a file does
```json
{
  "query_type": "file_explanation",
  "query": "explain the auth_service.py file"
}
```

**Best For:**
- Understanding complex files
- Onboarding to new codebases
- Documentation generation

---

### 4. Repository Summary
**Use Case:** Get high-level overview
```json
{
  "query_type": "repo_summary",
  "query": "summarize this repository"
}
```

**Best For:**
- Quick project understanding
- Architecture overview
- Technology stack identification

---

## Use Cases & Examples

### Use Case 1: Understanding API Endpoints
**Goal:** Find all REST API endpoints in the codebase

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me all REST API endpoints and their routes",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "code_search",
    "top_k": 10
  }'
```

**What you get:**
- List of all API route definitions
- HTTP methods (GET, POST, PUT, DELETE)
- Route paths and handlers
- Request/response schemas

---

### Use Case 2: Finding Authentication Logic
**Goal:** Understand how user authentication is implemented

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does user authentication and authorization work?",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "semantic_search",
    "top_k": 5
  }'
```

**What you get:**
- Authentication service implementation
- Token generation/validation logic
- Login/logout flows
- Authorization middleware

---

### Use Case 3: Database Schema Understanding
**Goal:** Learn about database models and relationships

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the database schema and model relationships",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "file_explanation",
    "top_k": 8
  }'
```

**What you get:**
- Database model definitions
- Table relationships
- Foreign keys and constraints
- Migration history

---

### Use Case 4: Integration Code Discovery
**Goal:** Find how external services are integrated

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How is GitHub API integrated in this project?",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "semantic_search",
    "top_k": 5
  }'
```

**What you get:**
- GitHub client implementation
- API wrapper code
- Authentication setup
- Example usage patterns

---

### Use Case 5: Error Handling Patterns
**Goal:** Understand error handling strategies

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me error handling and exception management code",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "code_search",
    "top_k": 10
  }'
```

**What you get:**
- Try-catch blocks
- Custom exception classes
- Error logging patterns
- Retry mechanisms

---

### Use Case 6: Configuration Management
**Goal:** Find all configuration files and settings

**Query:**
```bash
curl -X POST http://localhost:8000/api/vector-db/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List all configuration files and environment variables",
    "repository": "AM-Portfolio/ai-bots",
    "query_type": "semantic_search",
    "top_k": 10
  }'
```

**What you get:**
- Config file locations
- Environment variable definitions
- Default settings
- Configuration loaders

---

## API Reference

### 1. Index Repository
```http
POST /api/vector-db/index-repository
Content-Type: application/json

{
  "owner": "string",
  "repo": "string",
  "branch": "string",
  "collection": "string"
}
```

### 2. Semantic Search
```http
POST /api/vector-db/semantic-search
Content-Type: application/json

{
  "query": "string",
  "collection": "string",
  "top_k": number,
  "repository": "string",
  "language": "string"
}
```

### 3. GitHub-LLM Query
```http
POST /api/vector-db/query
Content-Type: application/json

{
  "query": "string",
  "repository": "string",
  "query_type": "semantic_search|code_search|file_explanation|repo_summary",
  "top_k": number
}
```

### 4. Check Status
```http
GET /api/vector-db/status
```

### 5. LLM Testing (Auto-Detection)
```http
POST /api/test/llm?prompt={query}&provider=together&show_thinking=true
```

**GitHub queries automatically detected:**
- Queries containing: `git`, `repo`, `repository`, `github`, `pr`, `pull request`
- Code-related queries: `api`, `code`, `function`, `class`, `method`
- Queries with repository references: `repo AM-Portfolio/ai-bots`, `in repository X`

---

## Troubleshooting

### Issue 1: "No documents in collection"
**Cause:** Vector DB is empty or was cleared on server restart

**Solution:**
```bash
# Re-index your repository
curl -X POST http://localhost:8000/api/vector-db/index-repository \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "AM-Portfolio",
    "repo": "ai-bots",
    "branch": "feature/bot-testing"
  }'
```

**⚠️ Important Note:** In-memory database clears on every server restart. Re-index after restarts.

---

### Issue 2: "0 results found" but documents are indexed
**Cause:** Repository filter mismatch

**Problem:**
```json
{
  "query": "api summary",
  "repository": "ai"  // ❌ Partial name doesn't match
}
```

**Solution:** Use full repository name
```json
{
  "query": "api summary",
  "repository": "AM-Portfolio/ai-bots"  // ✅ Full owner/repo
}
```

**Or search without repository filter:**
```json
{
  "query": "api summary",
  "top_k": 5
  // No repository filter - searches all indexed repos
}
```

---

### Issue 3: Slow indexing
**Cause:** Large repository with many files

**Solutions:**
- Index specific branches only
- Exclude large binary files (handled automatically)
- Use smaller repositories for testing
- Wait 2-5 minutes for medium repos (100-200 files)

---

### Issue 4: Query not detected as GitHub-related
**Cause:** Query doesn't contain GitHub keywords

**Solution:** Add explicit keywords:
```
❌ "show authentication"
✅ "show authentication code in repository"
✅ "explain the auth API implementation"
✅ "repo AM-Portfolio/ai-bots, show authentication"
```

---

### Issue 5: Poor search results
**Cause:** Query is too vague or doesn't match indexed content

**Solutions:**
1. **Be specific:**
   - ❌ "show me code"
   - ✅ "show me the FastAPI route handlers"

2. **Use technical terms:**
   - ❌ "how to save data"
   - ✅ "SQLAlchemy database model definitions"

3. **Increase `top_k`:**
   ```json
   {
     "query": "authentication",
     "top_k": 10  // Get more results
   }
   ```

4. **Remove filters:**
   ```json
   {
     "query": "authentication"
     // Remove repository and language filters
   }
   ```

---

## Advanced Features

### Filter by Programming Language
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database models",
    "collection": "github_repos",
    "language": "python",
    "top_k": 5
  }'
```

### Search Across Multiple Repositories
```bash
# Don't specify repository filter
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "API implementation patterns",
    "collection": "github_repos",
    "top_k": 10
  }'
```

### Get Raw Vector Search Results
```bash
# Use semantic-search endpoint for raw results without LLM processing
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "top_k": 5
  }'
```

---

## Best Practices

### 1. Index Strategically
- Index your main project repositories
- Index key dependencies you frequently reference
- Keep total indexed files under 10,000 for performance

### 2. Query Effectively
- Use specific technical terms
- Mention file types or languages when known
- Start with `top_k: 5`, increase if needed
- **Always use full repository name:** `owner/repo` format

### 3. Understand Query Types
- **Semantic Search**: Broad conceptual queries
- **Code Search**: Specific implementation queries
- **File Explanation**: Understanding specific files
- **Repo Summary**: High-level overview

### 4. Handle Restarts
- Re-index repositories after server restarts
- In-memory database doesn't persist
- Consider implementing persistence for production

### 5. Monitor Performance
- Check indexing status regularly
- Monitor query response times
- Track confidence scores in results

---

## Sample Queries for Common Tasks

### Code Review
```
"Find all TODO and FIXME comments in repo AM-Portfolio/ai-bots"
"Show error handling code that needs improvement"
"Identify deprecated function usage"
```

### Documentation
```
"Generate documentation for the API layer in AM-Portfolio/ai-bots"
"Explain the project architecture"
"List all public API endpoints"
```

### Onboarding
```
"What is the purpose of repository AM-Portfolio/ai-bots?"
"How do I set up the development environment?"
"Where is the main entry point of the application?"
```

### Debugging
```
"Find where database connections are created in AM-Portfolio/ai-bots"
"Show all places where User model is queried"
"Locate the error handling for HTTP 500 errors"
```

### Refactoring
```
"Find all duplicate code patterns"
"Show classes that violate single responsibility"
"List all database queries that could be optimized"
```

---

## Limitations

### Current Limitations
1. **In-Memory Storage**: Data cleared on restart
2. **Repository Name Matching**: Requires full `owner/repo` format
3. **File Size Limit**: 100KB per file
4. **No Real-Time Updates**: Must re-index for latest changes
5. **Language Support**: Works best with code files, may struggle with binary formats

### Planned Improvements
- Persistent vector database (ChromaDB, Pinecone)
- Fuzzy repository name matching
- Incremental updates without full re-indexing
- Real-time webhook integration with GitHub
- Advanced filtering (by author, date, tags)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API reference for correct usage
3. Examine server logs for detailed error messages
4. Ensure repositories are properly indexed before querying
5. **Always use full repository names** in the format `owner/repo`

---

**Last Updated:** October 18, 2025  
**Version:** 1.0.0
