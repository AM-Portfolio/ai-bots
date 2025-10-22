# Enhanced Summarization Examples

This directory contains sample code to demonstrate the **enhanced summarization** capabilities.

## 🎯 What Gets Extracted

### **Python Code** (`sample_code.py`)
The enhanced summarizer extracts:
- **Purpose**: User management service with async operations
- **Technical Details**: FastAPI, async/await, caching strategy
- **Business Logic**: Authentication and profile operations
- **Dependencies**: `fastapi`, `pydantic`, `asyncio`
- **Configuration**: `DATABASE_URL`, `CACHE_TTL` environment variables
- **Error Handling**: `HTTPException`, `ConnectionError`, custom error codes
- **Performance**: Redis caching with TTL configuration

**Example Summary Output:**
```
**Purpose**: User management service handling authentication and profile operations with async database queries and Redis caching.

**Technical Details**: Uses FastAPI HTTPException for error handling, implements async database operations with connection pooling, Redis caching layer with configurable TTL.

**Business Logic**: Retrieves user profiles by ID, handles user not found scenarios, manages cache invalidation.

**Dependencies**: fastapi, pydantic, asyncio, redis client

**Configuration**: DATABASE_URL (required), CACHE_TTL (default: 3600s)

**Error Handling**: 
- 404 NOT_FOUND for missing users
- 503 SERVICE_UNAVAILABLE for database connection failures
- 500 INTERNAL_SERVER_ERROR for unexpected errors

**API Interface**: async get_user_by_id(user_id: int) -> Optional[dict]

**Performance**: Implements two-tier caching (Redis + DB) to reduce database load, cache TTL configurable via environment variable.
```

---

### **Java/Spring Code** (`UserController.java`)
The enhanced summarizer extracts:
- **Purpose**: RESTful user management API
- **Technical Details**: Spring Boot, REST controller, validation
- **Business Logic**: CRUD operations for users
- **Annotations**: `@RestController`, `@GetMapping`, `@PostMapping`, `@Valid`, `@CrossOrigin`
- **API Endpoints**: 
  - `GET /api/v1/users/{id}`
  - `POST /api/v1/users`
  - `GET /api/v1/users` (with pagination)
  - `DELETE /api/v1/users/{id}`
- **Error Handling**: `UserNotFoundException`, `DuplicateEmailException`, `ValidationException`
- **Configuration**: CORS enabled, max page size enforced

**Example Summary Output:**
```
**Purpose**: REST API controller for user management with CRUD operations.

**Technical Details**: Spring Boot @RestController with @RequestMapping, uses dependency injection via @Autowired, implements RESTful design patterns.

**Business Logic**: Handles user creation, retrieval, listing with pagination, and deletion. Enforces business rules like unique email and max page size limits.

**Annotations**: @RestController, @RequestMapping("/api/v1/users"), @GetMapping, @PostMapping, @DeleteMapping, @Valid, @CrossOrigin

**API Endpoints**:
- GET /api/v1/users/{id} - Retrieve user by ID
- POST /api/v1/users - Create new user
- GET /api/v1/users?page=0&size=20 - List users with pagination
- DELETE /api/v1/users/{id} - Delete user (admin only)

**Error Handling**:
- UserNotFoundException → 404 Not Found
- DuplicateEmailException → 400 Bad Request
- Generic exceptions → 500 Internal Server Error

**Request/Response**: 
- Accepts: application/json with @Valid validation
- Returns: User entity or error status

**Performance**: Pagination support (default 20, max 100 items per page) to handle large datasets efficiently.

**Security**: CORS configured for cross-origin requests, DELETE endpoint requires admin role.
```

---

### **Docker Compose** (`docker-compose.yml`)
The enhanced summarizer extracts:
- **Purpose**: Multi-service application stack orchestration
- **Services**: app (main application), db (PostgreSQL), cache (Redis)
- **Networking**: Exposed ports 8000, 5432, 6379
- **Storage**: Named volume `postgres_data` for persistence
- **Environment**: Database credentials, Redis config, API keys
- **Dependencies**: App depends on db and cache services
- **Resources**: Redis with 256MB memory limit and LRU eviction

**Example Summary Output:**
```
**Purpose**: Docker Compose configuration for a 3-tier application with API, database, and caching.

**Services**:
1. **app**: Main application container
   - Build: Custom Dockerfile
   - Port: 8000:8000
   - Restart: unless-stopped
   
2. **db**: PostgreSQL 15 database
   - Image: postgres:15-alpine
   - Port: 5432:5432
   - Volume: postgres_data (persistent)
   
3. **cache**: Redis 7 cache
   - Image: redis:7-alpine
   - Port: 6379:6379
   - Memory: 256MB with LRU eviction

**Networking**: 
- App exposed on port 8000
- Database on 5432
- Cache on 6379
- Inter-service communication via service names

**Storage**:
- postgres_data volume for database persistence
- ./data volume mount for application data

**Environment**:
- DATABASE_URL: PostgreSQL connection string
- REDIS_URL: Redis connection string
- LOG_LEVEL: INFO
- API_KEY: Loaded from .env file

**Dependencies**: App service depends on db and cache (startup order enforced)

**Resources**: Redis configured with 256MB max memory and allkeys-lru eviction policy for automatic memory management.
```

---

## 🔍 Special File Type Detection

The enhanced summarizer automatically detects and applies specialized templates for:

### Infrastructure Files
- `Dockerfile` → Container build analysis
- `docker-compose.yml` → Service orchestration
- `helm/*.yaml` → Kubernetes Helm charts
- `k8s/*.yaml` → Kubernetes manifests

### API Specifications
- `openapi.yaml` / `swagger.json` → REST API contracts
- `*.proto` → gRPC/Protobuf definitions
- `schema.graphql` → GraphQL schemas

### Configuration Files
- `.env` / `.env.example` → Environment variables
- `application.yml` → Application config (Spring, etc.)
- `config.json` → JSON configuration
- `*.properties` → Java properties files

### Dependency Files
- `package.json` → npm dependencies
- `pom.xml` → Maven dependencies
- `build.gradle` → Gradle dependencies
- `requirements.txt` → Python dependencies
- `Cargo.toml` → Rust dependencies

### CI/CD
- `.github/workflows/*.yml` → GitHub Actions
- `.gitlab-ci.yml` → GitLab CI/CD
- `Jenkinsfile` → Jenkins pipelines

---

## 📊 Metadata Extraction

For each code file, the summarizer extracts:

1. **Imports/Dependencies**: External libraries and modules used
2. **Exceptions**: Error types handled or thrown
3. **Annotations**: Java/Kotlin/TypeScript decorators
4. **Environment Variables**: Configuration via env vars
5. **API Endpoints**: REST routes, GraphQL queries
6. **Config Keys**: Property access and settings

This metadata is **included in the embedding** alongside the summary, enabling:
- Dependency-aware search ("find all code using Redis")
- Error-handling search ("show exception handlers for UserNotFoundException")
- Config-aware search ("what uses DATABASE_URL?")
- API discovery ("list all POST endpoints")

---

## 🚀 How to Test

1. **Copy these examples to a test directory**:
   ```bash
   mkdir test-repo
   cp code-intelligence/examples/* test-repo/
   ```

2. **Run embedding pipeline**:
   ```bash
   python code-intelligence/embed_repo.py --repo test-repo --max-files 5
   ```

3. **Check the summaries in logs**:
   ```
   2025-10-22 11:30:15 - enhanced_summarizer - INFO - Generated summary for sample_code.py:chunk_0
   Purpose: User management service...
   Technical Details: Uses FastAPI...
   ```

4. **Query the results**:
   ```python
   from code_intelligence.vector_store import VectorStore
   
   store = VectorStore()
   results = store.search(query_embedding, limit=5)
   
   for r in results:
       print(f"File: {r['metadata']['file_path']}")
       print(f"Summary: {r['summary']}")
       print("---")
   ```

---

## 💡 Benefits

### **Before** (Basic Summarization):
```
"Function get_user_by_id in sample_code.py"
```

### **After** (Enhanced Summarization):
```
**Purpose**: User retrieval service with caching
**Technical**: FastAPI async with Redis cache
**Business**: Handles user profile access
**Config**: Requires DATABASE_URL, CACHE_TTL
**Errors**: HTTP 404 (not found), 503 (DB down), 500 (generic)
**Performance**: Two-tier caching to reduce DB load
```

The enhanced summaries provide **5-10x more context** for semantic search and code understanding!
