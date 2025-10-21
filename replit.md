# AI Development Agent

## Overview
This project is an intelligent, autonomous development agent designed to automate and streamline the software development lifecycle. It analyzes bugs, diagnoses issues, generates fixes, and manages documentation across platforms by integrating with services like GitHub, Jira, Grafana, and Confluence. Leveraging AI for analysis, code generation, and documentation, the agent provides an end-to-end solution for automated bug resolution and documentation publishing through REST API, webhooks, a Microsoft Teams bot, and a React-based frontend with voice interaction. The project aims to significantly enhance developer productivity and system reliability.

## User Preferences
- **Configuration Method**: ENV variables preferred over Replit connectors
- **LLM Provider**: Azure OpenAI as default primary provider with automatic fallback to Together AI and OpenAI. Role-based provider assignment (chat_provider, embedding_provider, beautify_provider) allows granular control.
- **Multilingual Support**: Automatic Hindi/English language detection enabled with language-aware responses
- **Vector Database**: Qdrant (persistent) preferred over in-memory for production use
- **UI Design**: Compact, space-efficient layouts with inline controls

## System Architecture
The project employs a clean architecture with a modular design for scalability and maintainability.

### Backend Architecture
-   **Framework:** FastAPI (Python 3.11).
-   **Core Layers:** Orchestration (parser, enricher, prompt builder, agent workflow), Enhanced GitHub Extractor, Interfaces (API, webhooks, bot), Features (business logic), Shared utilities, Data management, and Observability (Prometheus, OpenTelemetry).
-   **Database:** SQLAlchemy ORM supporting SQLite (default) and PostgreSQL with a repository pattern.
-   **AI Integration:** Factory pattern for pluggable LLM providers (Together AI, Azure OpenAI) with automatic fallback.
-   **Azure AI Services:** Comprehensive integration with both Service Endpoints (Speech, Translation) and Model Deployments (GPT-4o Transcribe, Model Router, GPT Audio Mini). Unified Azure AI Manager coordinates all services for complete workflows.
-   **Vector Database:** Qdrant (persistent, production-ready) with automatic fallback to in-memory when Docker is unavailable. Defaults to Qdrant with seamless degradation for environments without Docker support.
-   **Service Architecture:** Modular, LLM-powered service layer with `BaseService`, `ServiceManager`, and `ServiceLLMWrapper` for intelligent interactions across integrations like GitHub, Confluence, and MongoDB.
-   **Integration Wrappers:** Unified wrapper pattern for all external services (GitHub, Jira, Confluence) that uses ENV config by default and automatically falls back to Replit connectors. Makes integrations easily removable and switchable without changing business logic.
-   **Orchestration Layer:** Modular pipeline for message processing including `Message Parser` (with intelligent GitHub repository detection), `Context Enricher` (with caching), `Prompt Builder` (with templates), and a `LangGraph Agent` for task execution. Provides a unified facade for the pipeline and extensive structured logging.
-   **Intelligent Repository Matching:** Advanced fuzzy matching system that automatically resolves partial repository names to full paths. Supports compound word matching (e.g., "marketdata", "market data", "market-data" all match "am-market-data"), auto-loads repositories from GitHub organizations, and provides high-confidence matches using normalized similarity scoring.
-   **Logging:** Comprehensive structured logging with correlation IDs, method tracking, timing metrics, cache hit rates, and task execution status.

### Frontend Architecture
-   **Framework:** React 18 with TypeScript, built using Vite 5.
-   **Styling:** Tailwind CSS 3 with a modern vertical component architecture and compact, space-efficient layouts.
-   **UI/UX:** ChatGPT-like interface for LLM interaction with compact inline settings (model selection, show thinking, voice controls integrated with input area), collapsible responses with overview mode, professional panels for integrations, and consistent gradient backgrounds.
-   **Chat History:** Full conversation management with SQLite/PostgreSQL storage, sidebar navigation, and auto-save.
-   **Voice Assistant:** Advanced cloud-based voice assistant with OpenAI Whisper STT, intelligent intent classification, and OpenAI TTS. Features MediaRecorder-based audio capture, automatic pause detection (1.5s), session-based conversation context, and smart routing to commit workflow, GitHub-LLM, or general assistant based on user intent. Supports continuous conversation mode with automatic restart after each interaction.
-   **Navigation:** Streamlined 4-tab interface: Voice Assistant, LLM Testing, Integrations Hub, and Doc Orchestrator.
-   **LLM Testing Panel:** Compact design with inline controls (model selection, show thinking toggle, voice toggle), collapsible AI responses (overview/detail toggle), ReactMarkdown with syntax highlighting, and backend execution steps panel (visible when "Show Thinking" is enabled).
-   **Integrations Hub:** Unified, extensible system for managing integrations with a modern UI, live status bar, real-time updates, connection history, category-based organization, service cards, and a feature-rich configuration modal supporting various authentication types.
-   **Doc Orchestrator UI:** User-friendly interface for selective publishing to GitHub, Confluence, and Jira.
-   **API Client:** Axios-based HTTP client with strong TypeScript typing.
-   **Activity Logger:** Reactive logging system using Zustand for tracking user actions, API calls, and system events with a floating LogViewer component featuring filtering, expandable details, and performance tracking across all major flows (Chat, Voice, Integrations, LLM, API, Orchestrator, UI).

### Deployment
-   Configured for Autoscale deployment on Replit, with the FastAPI backend serving both API endpoints and the pre-built React frontend.

### Key Features
-   **Multi-Source Integration:** Connectors for GitHub, Jira, Confluence, and Grafana.
-   **AI-Powered Analysis:** Automated bug diagnosis, fix generation, test code generation, and documentation generation using LLMs.
-   **Resilient LLM Orchestration:** Automatic fallback across multiple LLM providers (Together AI → Azure OpenAI → OpenAI) with circuit breaker pattern, retry logic, and health tracking. If one provider fails, the system automatically tries alternative providers to ensure users always get a response.
-   **Comprehensive Azure AI Integration:** Dual integration approach combining Service Endpoints (Speech STT, Translation) and Model Deployments (GPT-4o Transcribe with diarization, Model Router, GPT Audio Mini). Unified Azure AI Manager orchestrates complex workflows: Voice Assistant (STT → Translation → Chat), Meeting Transcription (Diarization → Summarization), and Multilingual Chat (Translation → Chat → Translation back). All services have graceful fallback when credentials not configured.
-   **Resilient Vector DB:** Automatic fallback from Qdrant to in-memory when Docker is unavailable. Configured to attempt Qdrant connection first (for persistent storage), then gracefully degrade to in-memory mode in constrained environments like Replit.
-   **Automated Workflows:** End-to-end processes for context enrichment, root cause analysis, code fix generation, pull request creation, and command-driven documentation orchestration.
-   **Real-time Backend Activity Streaming:** Live visualization of orchestration pipeline execution via Server-Sent Events (SSE) with a `StreamingOrchestrationWrapper` and a `BackendActivityStream` React component.
-   **Thinking Process Visualization:** Shared backend component for tracking workflow steps, displayed via a reusable frontend `ThinkingProcess` component.
-   **GitHub Context Detection:** Advanced repository reference parser with fuzzy matching. Automatically detects repository mentions in natural language (e.g., "repo marketdata"), normalizes variants (one word, hyphenated, spaced), and resolves to full repository paths using intelligent compound word matching with 85% confidence scoring.
-   **Vector Database & Semantic Search:** Qdrant vector database (persistent, production-ready) with automatic fallback to in-memory mode. Supports 768-dimensional embeddings for GitHub repository code and documentation. Provides semantic search, code search, file explanation, and repository summarization with automatic indexing and intelligent query routing. When Docker is available, data persists across restarts; otherwise operates in-memory with seamless degradation.
-   **GitHub-LLM Orchestrator:** Specialized orchestration pipeline for GitHub-related queries with automatic detection, vector search integration, LLM-powered response generation, beautified and cleaned output. Provides 6-step workflow (planning, querying, synthesis, summary, beautification, cleaning) with comprehensive timing breakdowns and confidence scoring.
-   **Response Cleaner:** Automated text cleaning module that ensures proper markdown formatting, spacing, alignment, and line breaks in all LLM responses. Normalizes line breaks, fixes header/list/code block spacing, removes excessive whitespace, and optimizes paragraph structure.
-   **Automatic Query Detection:** Word-boundary pattern matching for GitHub-related queries in LLM Testing UI. Detects high-confidence keywords (git, repo, pr), medium-confidence code terms (api, function, class, method), and automatically routes to GitHub-LLM orchestrator without false positives.
-   **Intelligent Commit Workflow:** Advanced LangGraph-based system for intelligent GitHub commits, PRs, and documentation publishing. Features: (1) Natural language intent parsing (understands "commit and PR", "publish to Confluence", etc.), (2) Pre-commit templates for GitHub/Confluence/Jira, (3) UI approval system for write operations with 30-minute expiration, (4) Post-commit actions with clickable links and PR creation prompts, (5) PyGithub integration for reliable GitHub operations, (6) Template customization before commit, (7) Smart detection of platform and action from user messages. API endpoints: POST /api/commit/parse-intent, POST /api/commit/approve, GET /api/commit/pending-approvals.
-   **Voice Assistant Orchestration:** Complete voice interaction system with session management, OpenAI Whisper transcription, LLM-powered intent classification (routes to commit workflow, GitHub query, or general assistant), voice-optimized response formatting (summarized and conversational), and OpenAI TTS for natural speech synthesis. Backend API endpoints: POST /api/voice/session, POST /api/voice/process, GET /api/voice/session/{id}/history. Maintains conversation context across turns with configurable pause detection and response length limits.
-   **Documentation Orchestrator:** Automated workflow for creating branches, committing documentation to GitHub, publishing to Confluence, and creating Jira tickets, with clickable links to all generated artifacts.
-   **Observability:** Prometheus metrics, OpenTelemetry tracing, and comprehensive structured logging including request correlation IDs, LLM interaction logging, timing information, and enhanced flow tracking across Vector DB, GitHub-LLM, and Summary/Beautify layers.

## External Dependencies
-   **AI Providers:** Together AI, Azure OpenAI, OpenAI (for Whisper STT and TTS)
-   **Version Control:** GitHub
-   **Issue Tracking:** Jira
-   **Documentation:** Confluence
-   **Monitoring:** Grafana, Prometheus, OpenTelemetry
-   **Communication:** Microsoft Teams
-   **Database:** SQLAlchemy (for SQLite and PostgreSQL)
-   **Frontend Libraries:** React, Vite, Tailwind CSS, Lucide React, Axios
-   **Browser APIs:** MediaRecorder API, Web Speech Synthesis API (fallback)

## Documentation
-   **Azure AI Integration Guide:** Complete integration guide for Azure AI Services with both Service Endpoints and Model Deployments available in `AZURE_AI_INTEGRATION.md`. Includes configuration, API endpoints, usage examples, workflow recommendations, and testing instructions for Voice Assistant, Meeting Transcription, and Multilingual Chat workflows.
-   **Vector DB Usage Guide:** Comprehensive documentation for Vector Database and GitHub-LLM integration available in `VECTOR_DB_USAGE.md`. Includes quick start, API reference, use cases, troubleshooting, and best practices for indexing repositories and performing semantic code search.
-   **Qdrant Repository Indexing Guide:** Complete guide for setting up Qdrant with Docker Compose and re-indexing GitHub repositories available in `QDRANT_REPOSITORY_INDEXING.md`. Covers installation, configuration, repository indexing via REST API/UI/Python, re-indexing strategies, data persistence, backup/restore, troubleshooting, and best practices.

## Known Issues & Limitations
-   **Repository Name Matching:** Query filters require full `owner/repo` format. Partial repository names (e.g., "ai-bots") will not match stored documents (e.g., "AM-Portfolio/ai-bots").