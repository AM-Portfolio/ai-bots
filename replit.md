# AI Development Agent

## Overview

An intelligent, autonomous development agent that provides comprehensive code intelligence, automated issue resolution, and multi-platform integration. The system combines semantic code search, LLM-powered analysis, and automated documentation generation to streamline development workflows.

**Core Capabilities:**
- **Code Intelligence**: Semantic code search and embedding using vector databases (Qdrant) with tree-sitter parsing
- **Multi-Source Issue Resolution**: Analyze and fix issues from GitHub, Jira, and Grafana alerts
- **AI-Powered Analysis**: Uses Together AI (default) or Azure OpenAI for code diagnosis and fix generation
- **Automated Workflows**: PR creation, test generation, and documentation publishing
- **Voice Assistant**: Azure Speech-to-Text integration with multilingual support
- **Observability**: Prometheus metrics and OpenTelemetry tracing

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### 1. Frontend Architecture
**Technology**: React + Vite with TypeScript  
**Port**: 5000 (development), exposed via proxy to backend API  
**Key Features**:
- Real-time chat interface with markdown rendering
- Voice input/output capabilities
- Service connection management UI
- LLM testing playground with multilingual support

**Design Decision**: Separated frontend build process allows independent development and deployment. Vite provides fast HMR and optimized production builds.

### 2. Backend Architecture
**Technology**: FastAPI (Python)  
**Port**: 8000 (development), 9000 (production)  
**Pattern**: Modular vertical slices with shared infrastructure

**Core Modules**:
- **`interfaces/`** - API endpoints and external adapters (REST, webhooks, Teams bot)
- **`orchestration/`** - LLM workflow orchestration with modular pipeline (message parsing → context enrichment → prompt building → agent execution)
- **`code-intelligence/`** - Semantic code analysis with tree-sitter parsing and vector embeddings
- **`features/`** - Independent business capabilities (issue analysis, code generation, testing, documentation)
- **`shared/`** - Cross-cutting concerns (LLM providers, Azure services, logging, configuration)

**Design Decision**: Vertical slice architecture enables teams to work on features independently without tight coupling. Each feature encapsulates its own logic, data access, and API endpoints.

### 3. LLM Provider Strategy
**Pattern**: Factory pattern with auto-detection and fallback  
**Primary Provider**: Together AI (Llama-3.3-70B-Instruct-Turbo)  
**Fallback Provider**: Azure OpenAI (GPT-4.1-mini)

**Provider Selection Logic**:
1. Check `LLM_PROVIDER` environment variable (`auto`, `together`, `azure`)
2. If `auto`: Detect based on configured API keys
3. Fallback chain: Together AI → Azure OpenAI → Error

**Rationale**: Flexibility for different deployment environments while maintaining consistent interface through `BaseLLMProvider` abstraction.

### 4. Code Intelligence Pipeline
**Architecture**: Multi-stage pipeline with incremental updates

**Stages**:
1. **File Discovery** - Scan repository, filter by language and patterns
2. **Code Parsing** - Tree-sitter semantic parsing (Python, JS/TS, Java, Kotlin, Dart, C/C++)
3. **Summarization** - Enhanced LLM summaries with technical + business context
4. **Embedding Generation** - Batch processing with rate limiting
5. **Vector Storage** - Qdrant for semantic search

**Key Features**:
- Incremental updates (only changed files)
- Change prioritization (modified files processed first)
- Adaptive rate limiting with batching
- Special file detection (Docker, Helm, configs, API specs)
- Two-phase pipeline: summarize → embed
- DLQ (Dead Letter Queue) for failed files

**Design Decision**: Separating summarization from embedding allows reuse of summaries without regenerating embeddings. Tree-sitter provides accurate semantic parsing across multiple languages.

### 5. Vector Database Strategy
**Primary**: Qdrant (production-ready with HTTP/gRPC)  
**Fallback**: In-memory provider (development/testing)  
**Configuration**: `VECTOR_DB_PROVIDER` environment variable

**Collections**:
- `github_repos` - Repository code embeddings with metadata
- `code_intelligence` - General code intelligence data

**Design Decision**: Fallback to in-memory provider ensures development continues even without Qdrant instance. Factory pattern allows easy provider swapping.

### 6. Orchestration Pipeline
**Pattern**: Facade pattern with modular stages

**Workflow**:
```
User Message → Message Parser → Context Enricher → Prompt Builder → LangGraph Agent
```

**Components**:
- **Message Parser**: Extract references (GitHub URLs, Jira tickets, issue IDs)
- **Context Enricher**: Fetch data from GitHub/Jira/Confluence with caching
- **Prompt Builder**: Format enriched context for LLM with templates
- **LangGraph Agent**: Execute tasks with LLM coordination

**Design Decision**: Each stage is independently testable and replaceable. Caching at enricher level reduces API calls.

### 7. Service Integration Layer
**Pattern**: Service Manager with factory registration  
**Supported Services**:
- GitHub (PyGithub)
- Jira (atlassian-python-api)
- Confluence (atlassian-python-api)
- Azure Speech (speech-to-text, text-to-speech)
- Azure Translator (multilingual support)
- MongoDB (optional document storage)

**Connection Management**:
- Lazy initialization
- Health checks
- Automatic retry with exponential backoff
- Connection pooling

**Design Decision**: Centralized service manager simplifies testing and allows mock injection. Health checks enable proactive monitoring.

### 8. Data Persistence
**Primary Database**: PostgreSQL (SQLAlchemy ORM)  
**Optional**: MongoDB (document storage for flexible schemas)

**Schema**:
- `issues` - Tracked issues from various sources
- `analyses` - AI-generated root cause analyses
- `fixes` - Generated code fixes with tests
- `chat_conversations` - Conversation history
- `chat_messages` - Individual messages with metadata

**Design Decision**: PostgreSQL for structured data with ACID guarantees. MongoDB optional for unstructured/flexible data like logs or analytics.

### 9. Observability Stack
**Metrics**: Prometheus client (issues analyzed, fixes generated, LLM calls, duration histograms)  
**Tracing**: OpenTelemetry with FastAPI instrumentation  
**Logging**: Structured logging with context vars (request_id, user_id)

**Key Metrics**:
- `ai_dev_agent_issues_analyzed_total` (by source, severity)
- `ai_dev_agent_fixes_generated_total`
- `ai_dev_agent_llm_calls_total` (by operation)
- `ai_dev_agent_analysis_duration_seconds` (histogram)

**Design Decision**: Standard observability tools enable easy integration with existing monitoring infrastructure.

## External Dependencies

### Third-Party APIs
- **Together AI** - LLM inference (primary)
  - Model: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
  - Embedding: `togethercomputer/m2-bert-80M-32k-retrieval` (768 dims)
  
- **Azure OpenAI** - LLM inference (fallback)
  - Model: `gpt-4.1-mini`
  - Embedding: Azure OpenAI embedding models
  
- **Azure Speech Services**
  - Speech-to-Text with enhanced transcription
  - Text-to-Speech with voice synthesis
  
- **Azure Translator**
  - Multi-language translation
  - Language detection

- **GitHub API** - Repository access, issue tracking, PR creation
- **Jira API** - Ticket management
- **Confluence API** - Documentation publishing

### Vector Databases
- **Qdrant** - Production vector database (HTTP: 6333, gRPC: 6334)
- **In-Memory** - Development fallback

### Databases
- **PostgreSQL** - Primary relational database (port 5432)
- **MongoDB** - Optional document storage (port 27017)

### Infrastructure Services
- **Azure Key Vault** - Secrets management (optional)
- **Prometheus** - Metrics collection
- **OpenTelemetry** - Distributed tracing

### Development Tools
- **Docker Compose** - Container orchestration
- **Tree-sitter** - Code parsing (Python, JS/TS, Java, Kotlin, Dart, C/C++, Go, Rust)
- **Uvicorn** - ASGI server with hot reload

### Python Dependencies
**Core Framework**: FastAPI 0.109.0, Pydantic 2.5.3, SQLAlchemy 2.0.25  
**LLM Clients**: `openai` (1.10.0), `together` (latest)  
**Azure SDKs**: `azure-identity`, `azure-keyvault-secrets`  
**Service Integrations**: `PyGithub`, `jira`, `atlassian-python-api`  
**Monitoring**: `prometheus-client`, `opentelemetry-api`, `opentelemetry-sdk`  
**Utilities**: `aiohttp`, `httpx`, `redis`, `streamlit`

### Frontend Dependencies
**Framework**: React 18.2.0, TypeScript 5.2.2  
**Build Tool**: Vite 5.0.8  
**UI Libraries**: `lucide-react`, `react-icons`, `react-markdown`  
**State Management**: Zustand 5.0.8  
**HTTP Client**: Axios 1.6.0  
**Styling**: Tailwind CSS 3.3.6