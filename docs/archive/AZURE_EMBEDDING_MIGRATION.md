# Azure Embedding Migration Guide

## Overview
The system has been configured to use **Azure OpenAI embeddings** for all vector operations, replacing the previous Together AI embeddings.

## Changes Made

### 1. Configuration Updates
- **`.env`**: Set `EMBEDDING_PROVIDER=azure`
- **Embedding Model**: `text-embedding-ada-002` (1536 dimensions)
- **Use Case**: Optimized for technical documentation, code, and business content

### 2. Code Changes
- **`interfaces/vector_db_api.py`**: Vector DB initialization now uses Azure embeddings
- **`shared/vector_db/embedding_service.py`**: 
  - Dynamic dimension based on model (3072 for text-embedding-3-large, 1536 for ada-002)
  - Uses dedicated embedding API version from settings
  - Maintained Azure OpenAI client for embeddings
  - Batch embedding uses Azure SDK (no REST API needed for Azure)

### 3. Architecture
```
┌─────────────────────────────────────────────────────┐
│                 User Query                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Azure OpenAI Embeddings (text-embedding-3-large)   │
│  • Dimension: 3072 (highest quality)                │
│  • Optimized for: Code, technical docs, business    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│        Qdrant Vector DB (localhost:6333)            │
│  • Storage: Local (your machine)                    │
│  • Collection: github_repos                         │
│  • Vector Dimension: 1536 (Azure)                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  Azure OpenAI GPT-4.1-mini (Analysis/Chat)          │
│  • Response generation                              │
│  • Code explanation                                 │
│  • Beautification                                   │
└─────────────────────────────────────────────────────┘
```

## ⚠️ IMPORTANT: Re-indexing Required

### Why Re-index?
- **Old vectors**: 768 dimensions (Together AI)
- **New vectors**: 3072 dimensions (Azure OpenAI text-embedding-3-large)
- **Incompatible**: Cannot mix different dimensional vectors in same collection

### Steps to Re-index

#### Option 1: Delete and Re-index (Recommended)
```bash
# 1. Delete old collection data
curl -X DELETE "http://localhost:8000/api/vector-db/collection/github_repos"

# 2. Re-index your repositories
curl -X POST "http://localhost:8000/api/vector-db/index/repository" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "AM-Portfolio",
    "repo": "ai-portfolio",
    "branch": "main"
  }'
```

#### Option 2: Use Qdrant Directly
```bash
# Delete the collection in Qdrant
curl -X DELETE "http://localhost:6333/collections/github_repos"

# Restart your application (it will recreate with new dimensions)
python -m uvicorn interfaces.http_api:app --host 0.0.0.0 --port 8000
```

## Benefits of Azure Embeddings

### 1. **Technical Content Optimized**
- Better understanding of code syntax and structure
- Improved semantic matching for technical queries
- Enhanced accuracy for API documentation

### 2. **Business Content Support**
- Clear differentiation between technical and business terms
- Better context understanding for product descriptions
- Improved matching for requirement documents

### 3. **Higher Dimensional Space**
- 3072 dimensions vs 768 dimensions (4x more capacity)
- Most nuanced semantic relationships available
- Best separation of similar but distinct concepts
- Highest quality embeddings from OpenAI

### 4. **Unified Ecosystem**
- Same provider for embeddings and LLM analysis
- Consistent API versions and authentication
- Simplified credential management

## Configuration Details

### Azure OpenAI Settings
```ini
# Endpoint
AZURE_OPENAI_ENDPOINT=https://munis-mgzdcoho-eastus2.cognitiveservices.azure.com/

# Embedding Deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# API Version
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Provider Assignment
EMBEDDING_PROVIDER=azure
```

### Vector Database
```ini
# Qdrant (Local)
VECTOR_DB_PROVIDER=qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Verification Steps

### 1. Check Embedding Service
```bash
# Start the application and check logs
python -m uvicorn interfaces.http_api:app --host 0.0.0.0 --port 8000

# Look for:
# "🎯 Initializing embedding service with provider: azure"
# "• Model: text-embedding-ada-002"
# "• Dimension: 1536"
```

### 2. Test Embedding Generation
```bash
curl -X POST "http://localhost:8000/api/vector-db/test-embedding" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test technical documentation embedding"}'

# Should return 1536-dimensional vector
```

### 3. Verify Vector DB Dimension
```bash
# Check Qdrant collection info
curl "http://localhost:6333/collections/github_repos"

# Should show: "vector_size": 1536
```

## Troubleshooting

### Issue: "Dimension mismatch"
**Solution**: Delete the old collection and re-index all repositories

### Issue: "Azure OpenAI credentials not configured"
**Solution**: Check `.env` file has:
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`

### Issue: "Embedding generation failed"
**Solution**: 
1. Verify Azure deployment name matches your Azure AI Foundry deployment
2. Check API version is supported (2025-01-01-preview)
3. Ensure deployment is active in Azure portal

## Cost Considerations

### Azure OpenAI Embeddings Pricing
- **text-embedding-ada-002**: ~$0.0001 per 1K tokens
- **Batch processing**: Significantly more efficient
- **Comparison**: Similar to Together AI pricing

### Recommendations
- Use batch embedding for large repositories (already implemented)
- Monitor usage in Azure portal
- Consider caching frequently accessed embeddings

## Next Steps

1. ✅ **Configuration updated** - Azure embeddings enabled
2. ⏳ **Re-index repositories** - Delete old data and re-index
3. ⏳ **Test queries** - Verify improved semantic search
4. ⏳ **Monitor performance** - Compare with previous setup

## Support

For issues or questions:
1. Check application logs for detailed error messages
2. Verify Azure portal shows active deployments
3. Test with small repository first before indexing large ones
