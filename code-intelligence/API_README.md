# Code Intelligence API

The Code Intelligence API has been moved to the `code-intelligence` module for better organization and cleaner imports.

## Location
- **API Module**: `code-intelligence/api.py`
- **Endpoint Prefix**: `/api/code-intelligence`

## Benefits of this move:
1. ✅ **No import conflicts** - All code-intelligence modules are in the same directory
2. ✅ **Cleaner architecture** - API lives with the code it serves
3. ✅ **Easier maintenance** - Related code stays together
4. ✅ **No sys.path manipulation** - Direct imports work correctly
5. ✅ **Better auto-reload** - No circular import issues with uvicorn

## Endpoints

### POST `/api/code-intelligence/embed`
Embed a repository (local or GitHub) with enhanced summaries

### POST `/api/code-intelligence/query`
Query code using semantic search

### GET `/api/code-intelligence/status`
Get system status and statistics

### GET `/api/code-intelligence/health`
Health check endpoint

### DELETE `/api/code-intelligence/cleanup`
Cleanup/delete collection data

## Usage

See `/interfaces/API_EXAMPLES.md` for detailed usage examples.

## Integration

The API is automatically registered in `interfaces/http_api.py`:

```python
# Import from code-intelligence module
sys.path.insert(0, str(Path(__file__).parent.parent / "code-intelligence"))
from api import router as code_intelligence_router

# Register in FastAPI app
app.include_router(code_intelligence_router)
```
