# Code Intelligence Architecture - Using Shared Vector DB

## ✅ Current Architecture (Fully Integrated)

All code intelligence components now use the **shared vector_db infrastructure**. There are NO custom Qdrant clients in the code-intelligence module.

```
┌─────────────────────────────────────────────────────────────┐
│                    Code Intelligence                         │
│                  (code-intelligence/)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─→ orchestrator.py
                            │   └─→ Uses shared components
                            │
                            ├─→ embed_repo.py (EmbeddingOrchestrator)
                            │   ├─→ Uses shared EmbeddingService ✅
                            │   └─→ Uses VectorStore (wrapper)
                            │
                            └─→ vector_store.py (VectorStore)
                                └─→ Uses shared VectorDBFactory ✅
                                    └─→ Creates VectorDBProvider
                                        └─→ QdrantProvider

┌─────────────────────────────────────────────────────────────┐
│                 Shared Infrastructure                        │
│                    (shared/)                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─→ vector_db/
                            │   ├─→ factory.py (VectorDBFactory)
                            │   ├─→ base.py (VectorDBProvider interface)
                            │   ├─→ embedding_service.py (EmbeddingService)
                            │   └─→ providers/
                            │       └─→ qdrant_provider.py ✅ ONLY place with QdrantClient
                            │
                            └─→ code_intelligence/
                                ├─→ service.py (CodeIntelligenceService)
                                ├─→ models.py
                                └─→ README.md
```

## Components Analysis

### ✅ 1. code-intelligence/vector_store.py
**Status**: Uses shared VectorDBProvider

```python
# Line 18-19
from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.base import VectorDBProvider, DocumentMetadata, VectorSearchResult

# Line 73-80
self.provider: VectorDBProvider = VectorDBFactory.create(
    provider_type="qdrant",
    host=host,
    port=port
)
```

**No direct Qdrant imports** ✅

### ✅ 2. code-intelligence/embed_repo.py
**Status**: Uses shared EmbeddingService

```python
# Line 28
from shared.vector_db.embedding_service import EmbeddingService

# Line 84-87
logger.info(f"📦 Initializing embedding service (provider: {embedding_provider})...")
self.embedding_service = EmbeddingService(provider=embedding_provider)

embedding_dim = self.embedding_service.get_dimension()
```

**No direct OpenAI/Azure client** ✅

### ✅ 3. code-intelligence/orchestrator.py
**Status**: Uses shared components through EmbeddingOrchestrator

```python
# Line 31-33
from vector_store import VectorStore
from shared.vector_db.embedding_service import EmbeddingService
from shared.config import settings
```

**Orchestrates shared components** ✅

### ✅ 4. shared/code_intelligence/service.py
**Status**: NEW - Fully integrated service

```python
# Line 14-15
from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.base import VectorDBProvider

# Line 17
from shared.azure_services.model_deployment_service import AzureModelDeploymentService

# Line 54-58
self.provider: VectorDBProvider = VectorDBFactory.create(
    provider_type=vector_db_type,
    host=qdrant_host,
    port=qdrant_port
)
```

**100% shared infrastructure** ✅

## ✅ No Custom Vector DB Clients

**Grep results confirm:**
```bash
# Search for direct Qdrant usage in code-intelligence/
grep -r "QdrantClient" code-intelligence/
# Result: NO MATCHES ✅

grep -r "from qdrant_client import" code-intelligence/
# Result: NO MATCHES ✅

grep -r "import qdrant" code-intelligence/
# Result: NO MATCHES ✅
```

**Only legitimate QdrantClient usage:**
- `shared/vector_db/providers/qdrant_provider.py` - Implementation of provider interface ✅
- `shared/tests/test_vector.py` - Unit tests ✅

## Data Flow

### Embedding Pipeline (code-intelligence CLI)

```
1. orchestrator.py embed
   │
   ├─→ EmbeddingOrchestrator (embed_repo.py)
   │   │
   │   ├─→ shared.vector_db.embedding_service.EmbeddingService
   │   │   └─→ Creates embeddings via Azure OpenAI
   │   │
   │   └─→ VectorStore (vector_store.py)
   │       └─→ shared.vector_db.factory.VectorDBFactory
   │           └─→ shared.vector_db.providers.qdrant_provider.QdrantProvider
   │               └─→ QdrantClient (only here!)
   │
   └─→ Stores in Qdrant: localhost:6333
```

### Query API (REST endpoints)

```
2. POST /api/code-intelligence/query
   │
   ├─→ code_intelligence_query_api.py
   │   │
   │   └─→ shared.code_intelligence.CodeIntelligenceService
   │       │
   │       ├─→ shared.azure_services.model_deployment_service (embeddings)
   │       │
   │       └─→ shared.vector_db.factory.VectorDBFactory
   │           └─→ shared.vector_db.providers.qdrant_provider.QdrantProvider
   │               └─→ QdrantClient (only here!)
```

## Benefits of Shared Architecture

✅ **Single source of truth** - One VectorDBProvider interface
✅ **Easy provider switching** - Change from Qdrant to Pinecone/Weaviate
✅ **Consistent error handling** - Centralized retry logic
✅ **Unified configuration** - Settings in shared/config
✅ **No code duplication** - Reuse embedding service
✅ **Better testing** - Mock VectorDBProvider interface
✅ **Cleaner dependencies** - No qdrant_client in code-intelligence/

## Configuration

All vector DB configuration is centralized:

**shared/config/settings.py:**
```python
# Vector DB settings
vector_db_type = "qdrant"
qdrant_host = "localhost"
qdrant_port = 6333

# Embedding settings
azure_openai_embedding_deployment = "text-embedding-3-large"
embedding_dimension = 3072
```

**code-intelligence/** uses these settings through shared infrastructure.

## Migration Complete ✅

The code-intelligence module has been fully migrated to use shared vector_db components:

- ❌ No custom QdrantClient usage
- ❌ No custom embedding clients
- ❌ No duplicate vector DB logic
- ✅ All operations through VectorDBFactory
- ✅ All embeddings through EmbeddingService
- ✅ Clean separation of concerns
- ✅ Consistent error handling

## Testing

Verify the integration:

```powershell
# 1. Check architecture
python diagnose_code_intelligence.py

# 2. Run embedding (uses shared components)
python code-intelligence/orchestrator.py embed

# 3. Test query API (uses shared components)
curl -X POST http://localhost:8000/api/code-intelligence/query `
  -H "Content-Type: application/json" `
  -d '{"query": "test", "limit": 5}'
```

All operations will use the shared VectorDBProvider infrastructure!
