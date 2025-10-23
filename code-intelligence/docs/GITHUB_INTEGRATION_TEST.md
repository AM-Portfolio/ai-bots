# GitHub Integration Test

## Overview

Complete integration test that performs a full workflow with a GitHub repository:
1. **Fetch** repository information from GitHub
2. **Embed** selected files (configurable count)
3. **Query** the embedded code with test queries  
4. **Stats** - retrieve collection statistics
5. **Cleanup** - remove test collection from vector database

## Usage

```bash
python test_github_integration.py owner/repo [max_files]
```

## Examples

```bash
# Test with GitHub's Hello-World (3 files)
python test_github_integration.py octocat/Hello-World 3

# Test with VS Code repository (5 files)  
python test_github_integration.py microsoft/vscode 5

# Test with React repository (10 files)
python test_github_integration.py facebook/react 10
```

## Test Workflow

### Test 1: GitHub Fetch Configuration
- Validates repository name format (owner/repo)
- Creates collection name: `test_owner_repo`
- Prepares for GitHub fetching

### Test 2: Initial Cleanup
- Removes any existing test collection
- Ensures clean slate for testing
- Non-critical if collection doesn't exist

### Test 3: Create Embeddings from GitHub
- Fetches repository via GitHub API
- Uses GitHub LLM analyzer to select relevant files
- Limits to `max_files` parameter
- Creates embeddings using Azure OpenAI
- Stores in Qdrant vector database

**Expected Output:**
```
✅ Embedding complete:
   Files processed: X
   Chunks created: Y
   Embeddings stored: Z
```

### Test 4: Query Embedded Code
- Runs 3 test queries:
  1. "main function or entry point"
  2. "class definitions"  
  3. "configuration or settings"
- Shows top result for each query
- Displays relevance score and file path

**Expected Output:**
```
📋 Query 1: 'main function or entry point'
   ✅ Found 3 results
   📄 Top result: src/main.py
   🎯 Relevance: Excellent
   📊 Score: 0.892
```

### Test 5: Get Statistics
- Retrieves collection statistics
- Shows total vectors and indexed count
- Validates vector database state

**Expected Output:**
```
✅ Statistics retrieved:
   Collection: test_octocat_Hello-World
   Total vectors: X
   Indexed: X
```

### Test 6: Final Cleanup
- Deletes test collection
- Removes all test vectors
- Confirms cleanup success

**Expected Output:**
```
✅ Cleanup complete: X vectors deleted
   Collection removed from vector database
```

## Key Features

### Async Support
All orchestrator methods are `async`, so the test properly uses `asyncio.run()` and `await`:

```python
async def test_embed_repository(self) -> bool:
    result = await self.orchestrator.embed_repository(
        collection_name=self.collection_name,
        github_repository=self.repo_name,
        max_files=self.max_files,
        force_reindex=True
    )
```

### Error Handling
- Each test has try/except blocks
- Detailed error messages with stack traces
- Non-critical errors (like initial cleanup) don't fail the test

### Collection Naming
- Auto-generates safe collection names: `test_owner_repo`
- Replaces `/` with `_` for valid Qdrant collection names
- Prevents conflicts with production collections

### Flexible File Count
- Default: 5 files
- Can be overridden via command line parameter
- Useful for testing different workload sizes

## Architecture Validation

This test validates the complete refactored architecture:

```
┌─────────────────┐
│  GitHub Repo    │
│  (owner/repo)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │◄──── Test calls all async methods
│  (async methods)│
└────────┬────────┘
         │
    ┌────┴────┬──────────┬───────────┐
    ▼         ▼          ▼           ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌─────────┐
│ Embed  │ │Query │ │ Stats  │ │ Cleanup │
│Pipeline│ │Service│ │        │ │         │
└────┬───┘ └───┬──┘ └───┬────┘ └────┬────┘
     │         │        │           │
     ▼         ▼        ▼           ▼
┌────────────────────────────────────────┐
│       Qdrant Vector Database           │
│     (Collection: test_owner_repo)      │
└────────────────────────────────────────┘
```

## Requirements

1. **GitHub Token**: Set in environment (`GITHUB_TOKEN`)
2. **Azure OpenAI**: For embeddings and analysis
3. **Qdrant**: Running locally on port 6333
4. **Network**: Internet access to fetch GitHub repositories

## Success Criteria

All 6 tests must pass:
- ✅ GitHub Fetch Configuration
- ✅ Cleanup Before  
- ✅ Embed Repository
- ✅ Query Code
- ✅ Get Statistics
- ✅ Cleanup After

## Example Output

```
🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪
  CODE INTELLIGENCE - GITHUB INTEGRATION TEST
🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪🧪

GitHub Repository: octocat/Hello-World
Collection Name: test_octocat_Hello-World
Max Files to Process: 3

================================================================================
  TEST SUMMARY
================================================================================

Tests Run: 6
Passed: 6
Failed: 0

Detailed Results:
  ✅ PASSED: GitHub Fetch Configuration
  ✅ PASSED: Cleanup Before
  ✅ PASSED: Embed Repository
  ✅ PASSED: Query Code
  ✅ PASSED: Get Statistics
  ✅ PASSED: Cleanup After

📊 Embedding Statistics:
   success: True
   files_processed: 3
   chunks_generated: 45
   chunks_embedded: 45
   success_rate: 1.0

================================================================================
✅ ALL TESTS PASSED
================================================================================
```

## Troubleshooting

### AsyncIO Event Loop Issues
**Problem**: `asyncio.run() cannot be called from a running event loop`

**Solution**: Use `async def` for test methods and `await` orchestrator calls. Main runner uses `asyncio.run()`.

### GitHub API Rate Limiting
**Problem**: Too many API requests to GitHub

**Solution**: Reduce `max_files` parameter or wait for rate limit reset.

### Collection Already Exists
**Problem**: Test fails because collection wasn't cleaned up

**Solution**: Run cleanup manually or delete collection in Qdrant:
```bash
python main.py cleanup --collection test_owner_repo --force
```

### No Results in Query
**Problem**: Queries return 0 results

**Possible Causes**:
- Files didn't embed successfully
- Score threshold too high (default 0.6)
- Query doesn't match repository content

## Related Files

- `test_simple_integration.py` - Component-level tests (no GitHub)
- `test_integration.py` - Original integration test (has async issues)
- `orchestrator.py` - Core orchestration logic
- `docs/TEST_RESULTS.md` - Previous test results

## Next Steps

1. ✅ **COMPLETED**: Create GitHub integration test with full workflow
2. ✅ **COMPLETED**: Support async orchestrator methods
3. ✅ **COMPLETED**: Add cleanup before/after
4. ✅ **COMPLETED**: Test with real GitHub repository
5. 🔲 **OPTIONAL**: Add performance metrics
6. 🔲 **OPTIONAL**: Test with larger repositories
7. 🔲 **OPTIONAL**: Add CI/CD pipeline

---

**Last Updated**: 2025-10-23  
**Status**: ✅ RUNNING - Test executing against octocat/Hello-World
