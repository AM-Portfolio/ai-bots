# Known Issues with Integration Tests

## Summary

The GitHub integration test revealed several architectural issues that need to be addressed before full async integration testing is possible.

## Issues Discovered

### 1. AsyncIO Event Loop Conflicts ❌

**Problem**: `asyncio.run() cannot be called from a running event loop`

**Location**: `storage/vector_store.py` lines 98, 277, 342, 369

**Root Cause**: VectorStore uses `asyncio.run()` in `__init__` and other methods:
- Line 98: `asyncio.run(self._async_init())`
- Line 277: `asyncio.run(self._async_search(...))`
- Line 342: `asyncio.run(self.provider.get_collection_stats(...))`
- Line 369: `asyncio.run(self.provider.health_check())`

**Impact**: Cannot use VectorStore from within async context (which orchestrator methods are)

**Workaround**: 
- Use CLI commands which run in synchronous context
- Or refactor VectorStore to use async/await properly

**Proper Fix** (requires refactoring):
```python
# In VectorStore.__init__
def __init__(self, ...):
    # Don't call async init here
    self._initialized = False
    
async def ensure_initialized(self):
    if not self._initialized:
        await self._async_init()
        self._initialized = True

# Then in all methods:
async def search(self, ...):
    await self.ensure_initialized()
    # ... rest of method
```

### 2. FallbackParser Missing Method ❌

**Problem**: `'FallbackParser' object has no attribute 'parse'`

**Location**: `parsers/fallback_parser.py` (inferred)

**Root Cause**: FallbackParser doesn't implement the `parse()` method that CodeParser expects

**Impact**: Files fall back to FallbackParser when tree-sitter fails, but then parsing still fails

**Files Affected**:
- ui/app.py
- code-intelligence/main.py
- main.py

**Proper Fix**:
```python
# In FallbackParser class
def parse(self, code: str, file_path: str) -> List[CodeChunk]:
    """
    Fallback parsing using simple heuristics.
    """
    # Implement basic parsing logic
    chunks = []
    lines = code.split('\n')
    # ... create chunks based on simple patterns
    return chunks
```

### 3. Division by Zero in Summary Batcher ❌

**Problem**: `ZeroDivisionError: division by zero`

**Location**: `utils/summary_batcher.py` line 80

**Root Cause**: When no chunks are parsed (due to parser failure), total_count is 0

**Code**:
```python
logger.info(f"   📊 Starting: {total_processed}/{total_count} complete ({(total_processed/total_count)*100:.1f}%)")
```

**Proper Fix**:
```python
if total_count > 0:
    percentage = (total_processed/total_count)*100
    logger.info(f"   📊 Starting: {total_processed}/{total_count} complete ({percentage:.1f}%)")
else:
    logger.info(f"   📊 Starting: No items to process")
```

### 4. Tree-sitter Parser Initialization Warnings ⚠️

**Problem**: `'tree_sitter.Parser' object has no attribute 'language'`

**Impact**: Low - falls back to FallbackParser, but FallbackParser is broken (see issue #2)

**Languages Affected**:
- Python
- JavaScript  
- Java

**Note**: Kotlin and Dart show "not available" which is expected

## Test Results

### Working ✅
- GitHub Fetch Configuration
- Initial Cleanup (with warnings)
- Query Code (execution, but no results due to no embeddings)

### Failing ❌
- Embed Repository (parser + division by zero)
- Get Statistics (asyncio conflict)
- Final Cleanup (asyncio conflict)

## Workarounds

### For Testing

Use the simple integration test instead:
```bash
python test_simple_integration.py
```

This tests:
- Component initialization
- File discovery
- Query service interface  
- Enhanced summarizer interface

**Result**: ✅ 4/4 PASSED

### For GitHub Repository Testing

Use CLI commands directly (they work because they don't nest async):

```bash
# Embed repository from GitHub
python main.py embed --github-repo octocat/Hello-World --max-files 3

# Query the embedded code
python main.py query "main function" --limit 5

# Get statistics
python main.py health

# Cleanup
python main.py cleanup --collection code_intelligence --force
```

## Recommended Fixes (Priority Order)

### High Priority
1. **Fix FallbackParser** - Add `parse()` method so fallback actually works
2. **Fix VectorStore async** - Replace `asyncio.run()` with proper async/await pattern

### Medium Priority
3. **Fix division by zero** - Add zero-check in summary_batcher.py
4. **Fix tree-sitter** - Investigate why parsers can't set language attribute

### Low Priority
5. Add retry logic for transient failures
6. Add connection pooling for Azure services
7. Improve error messages

## Current Status

**Simple Integration Test**: ✅ **PASSING** (4/4 tests)
- Tests component interfaces
- No async conflicts
- No GitHub dependencies

**GitHub Integration Test**: ❌ **BLOCKED**
- Requires VectorStore refactoring
- Requires FallbackParser fix
- Requires summary_batcher fix

## Next Steps

1. Use `test_simple_integration.py` for CI/CD
2. Use CLI commands for manual GitHub testing
3. Create tickets for the 4 high/medium priority fixes
4. Revisit `test_github_integration.py` after fixes

---

**Last Updated**: 2025-10-23  
**Status**: DOCUMENTED - Known issues identified and workarounds provided
