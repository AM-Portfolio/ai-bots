# Cleanup Command - Remove Indexed Data

## Overview

The cleanup command allows you to permanently delete indexed data from the vector database by collection name or GitHub repository name.

## ⚠️ WARNING

**This operation is PERMANENT and CANNOT be undone!**
- All embeddings in the specified collection will be deleted
- The collection itself will be removed from the vector database
- Requires explicit `--force` flag to prevent accidental deletion

## Usage

### By Collection Name

```bash
# Delete a collection (requires --force)
python code-intelligence/main.py cleanup --collection my_project --force

# Preview what will be deleted (without --force)
python code-intelligence/main.py cleanup --collection my_project
```

### By GitHub Repository

```bash
# Delete by repository name (auto-converts to collection name)
python code-intelligence/main.py cleanup --repository owner/repo --force

# The repository "AM-Portfolio/ai-bots" becomes collection "am_portfolio_ai_bots"
python code-intelligence/main.py cleanup --repository AM-Portfolio/ai-bots --force
```

### Python API

```python
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator

orchestrator = CodeIntelligenceOrchestrator()

# Delete by collection name
result = await orchestrator.cleanup(
    collection_name="my_project",
    confirm=True  # Must be True to proceed
)

# Delete by repository
result = await orchestrator.cleanup(
    github_repository="owner/repo",
    confirm=True
)

# Check result
if result["success"]:
    print(f"Deleted {result['vectors_deleted']} vectors")
else:
    print(f"Error: {result['error']}")
```

## Safety Features

### 1. Confirmation Required
The `--force` flag (or `confirm=True` in API) is required to proceed:

```bash
# This will only show a warning
python main.py cleanup --collection my_project

# This will actually delete
python main.py cleanup --collection my_project --force
```

### 2. Statistics Before Deletion
Shows how many vectors will be deleted:

```
⚠️  WARNING: This will permanently delete all embeddings!
   Target: my_project
   Vectors: 1,234

To proceed, add --force flag:
   python main.py cleanup --collection my_project --force
```

### 3. Result Confirmation
After deletion, shows what was removed:

```
✅ Cleanup Complete!
============================================================
   Collection: my_project
   Vectors deleted: 1,234

   Collection 'my_project' has been permanently deleted.
```

## Repository Name Conversion

GitHub repository names are automatically converted to valid collection names:

| Repository | Collection Name |
|------------|----------------|
| `owner/repo` | `owner_repo` |
| `AM-Portfolio/ai-bots` | `am_portfolio_ai_bots` |
| `my-org/my-project` | `my_org_my_project` |

Rules:
- `/` replaced with `_`
- `-` replaced with `_`
- Converted to lowercase

## Examples

### Example 1: Clean Up Test Data
```bash
# After testing, remove test embeddings
python main.py cleanup --collection test_data --force
```

### Example 2: Re-index Repository
```bash
# Delete old embeddings
python main.py cleanup --collection my_project --force

# Re-embed with fresh data
python main.py embed --collection my_project
```

### Example 3: Remove Specific Repository
```bash
# Delete embeddings for a GitHub repository
python main.py cleanup --repository microsoft/vscode --force
```

### Example 4: Batch Cleanup Script
```python
import asyncio
from code_intelligence.orchestrator import CodeIntelligenceOrchestrator

async def cleanup_multiple():
    orchestrator = CodeIntelligenceOrchestrator()
    
    collections = ["old_project", "test_data", "deprecated"]
    
    for collection in collections:
        result = await orchestrator.cleanup(
            collection_name=collection,
            confirm=True
        )
        print(f"{collection}: {result['success']}")

asyncio.run(cleanup_multiple())
```

## Error Handling

### Collection Not Found
```json
{
  "success": false,
  "collection_name": "nonexistent",
  "error": "Collection does not exist"
}
```

### Missing Parameters
```json
{
  "success": false,
  "error": "Either collection_name or github_repository must be provided"
}
```

### No Confirmation
```json
{
  "success": false,
  "error": "Deletion not confirmed. Set confirm=True to proceed.",
  "collection_name": "my_project",
  "warning": "This will permanently delete all embeddings in this collection!"
}
```

## Best Practices

1. **Always Verify First**: Run without `--force` to see what will be deleted
2. **Backup Important Data**: Consider exporting embeddings before cleanup
3. **Use Specific Names**: Use descriptive collection names for easy identification
4. **Document Cleanup**: Keep records of when and why collections were deleted
5. **Test in Staging**: Test cleanup commands in a non-production environment first

## Related Commands

```bash
# Check what's in a collection before cleanup
python main.py query "test" --collection my_project

# Get collection statistics
# (orchestrator.get_stats("my_project"))

# Re-embed after cleanup
python main.py embed --collection my_project
```

## Integration

The cleanup command is fully integrated with:
- ✅ Main CLI (`main.py cleanup`)
- ✅ Orchestrator API (`orchestrator.cleanup()`)
- ✅ Vector Store (`vector_store.delete_collection()`)
- ✅ Qdrant Provider (underlying deletion)
