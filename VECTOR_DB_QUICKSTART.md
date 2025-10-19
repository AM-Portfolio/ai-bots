# Vector Database Quick Start

## ✅ What's Working

The Vector Database system is **fully functional** with the following capabilities:

### Core Features
- ✅ **GitHub Repository Indexing** - Fetches and indexes repository content
- ✅ **Semantic Search** - Search by meaning, not just keywords
- ✅ **GitHub-LLM Orchestration** - Intelligent query planning and execution
- ✅ **Response Beautification** - LLM-powered formatting
- ✅ **Multiple Providers** - In-Memory (dev) and ChromaDB (production)

### API Endpoints
1. `GET /api/vector-db/status` - Check system status
2. `GET /api/vector-db/examples` - Get example repositories
3. `POST /api/vector-db/index-repository` - Index a repository
4. `POST /api/vector-db/semantic-search` - Perform semantic search
5. `POST /api/vector-db/query` - Intelligent GitHub-LLM query

## ⚠️ Known Issue: "Bad Gateway" During Indexing

**Problem**: When indexing repositories, you may get a "502 Bad Gateway" error. This happens because:

1. **Long Processing Time**: Indexing fetches every file from GitHub and generates embeddings, which can take 2-10 minutes depending on repository size
2. **HTTP Timeout**: Your browser/client times out before the process completes
3. **Blocking Operation**: The current implementation processes files synchronously

**Important**: Even though you get a timeout error, **the indexing continues in the background**. The server doesn't stop - it keeps processing.

## 🚀 How to Use Successfully

### Option 1: Use Smaller Repositories (Recommended)
Start with repositories under 200 files for faster results:

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

**Small Repositories to Try**:
- `psf/requests` (Python HTTP library, ~150 files)
- `kelseyhightower/nocode` (Minimal repo, < 10 files)
- `tiangolo/fastapi` (Modern Python framework, ~300 files)

### Option 2: Test with API Documentation
Visit the interactive API docs to test endpoints with built-in timeout handling:
```
http://localhost:8000/docs
```

Navigate to `/api/vector-db/index-repository` and use the "Try it out" feature.

### Option 3: Check Status After Indexing
Even if you get a timeout, check the status to see if documents were indexed:

```bash
curl http://localhost:8000/api/vector-db/status
```

Look for the `count` field in the response:
```json
{
  "provider": "in-memory",
  "initialized": true,
  "collections": [
    {
      "name": "github_repos",
      "count": 45,  // <-- Number of indexed documents
      "dimension": 768
    }
  ]
}
```

## 📊 For Your Repository: AM-Portfolio/am-portfolio

### Current Situation
- **Repository Size**: Unknown (need to check)
- **Error**: 502 Bad Gateway (timeout)
- **Cause**: Indexing takes longer than HTTP timeout (usually 60-120 seconds)

### Recommended Approach

**Step 1**: Check repository size first
```bash
curl -s https://api.github.com/repos/AM-Portfolio/am-portfolio | \
  jq '{size: .size, default_branch: .default_branch, language: .language}'
```

**Step 2**: Use the API docs for better timeout handling
1. Go to `https://your-replit-url:8000/docs`
2. Find `POST /api/vector-db/index-repository`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "owner": "AM-Portfolio",
     "repo": "am-portfolio",
     "branch": "main",
     "collection": "github_repos"
   }
   ```
5. Click "Execute"

**Step 3**: Monitor progress in server logs
The indexing will continue even if the HTTP request times out. Watch the Replit console logs for progress indicators like:
- `📂 Successfully retrieved X items`
- `📝 Found X files to index`
- `✅ Successfully indexed X documents`

## 🎯 Full Working Example

Here's a complete workflow that **works**:

### 1. Get Examples
```bash
curl http://localhost:8000/api/vector-db/examples
```

### 2. Index Small Repository
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

### 3. Check Status
```bash
curl http://localhost:8000/api/vector-db/status
```

### 4. Perform Semantic Search
```bash
curl -X POST http://localhost:8000/api/vector-db/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to make HTTP GET requests",
    "collection": "github_repos",
    "top_k": 3
  }'
```

## 🔧 Technical Details

### Why It Takes Long
For a repository with 200 files:
1. Fetch repository tree from GitHub: ~2 seconds
2. Filter indexable files: <1 second
3. **Fetch each file content**: 200 × 0.5s = 100 seconds
4. **Generate embeddings**: 200 × 1s = 200 seconds (using LLM)
5. Store in vector DB: ~2 seconds

**Total**: ~300 seconds (5 minutes) for 200 files

### What's Indexed
- **Code Files**: .py, .js, .ts, .jsx, .tsx, .java, .go, .rs, .c, .cpp, .cs, .rb, .php, .swift
- **Documentation**: .md, .rst, .txt
- **Configuration**: .yaml, .yml, .json, .toml
- **Excluded**: Images, binaries, very large files (>500KB)

## 💡 Future Improvements

To fix the timeout issue, these improvements are planned:
1. **Async Background Jobs**: Use Celery or background tasks
2. **Progress Tracking**: Real-time progress updates via WebSocket/SSE
3. **Batch Processing**: Process files in parallel batches
4. **Caching**: Cache embeddings for unchanged files
5. **Status Endpoint**: Check indexing progress

## 📝 Summary

✅ **What Works**: GitHub repo indexing, semantic search, LLM orchestration
⚠️ **Known Issue**: HTTP timeouts for large repositories (indexing continues in background)
🎯 **Best Practice**: Start with small repos, check status endpoint after timeouts
📚 **Full Docs**: See `VECTOR_DB_USAGE.md` for complete API documentation
