# AI Development Agent

## Overview
This project is an intelligent, autonomous development agent designed to automate and streamline the software development lifecycle. It analyzes bugs, diagnoses issues, generates fixes, and manages documentation across platforms by integrating with services like GitHub, Jira, Grafana, and Confluence. Leveraging AI for analysis, code generation, and documentation, the agent provides an end-to-end solution for automated bug resolution and documentation publishing through REST API, webhooks, a Microsoft Teams bot, and a React-based frontend with voice interaction. The project aims to significantly enhance developer productivity and system reliability.

## User Preferences
- **Configuration Method**: ENV variables preferred over Replit connectors
- **LLM Provider**: Together AI as primary provider with automatic fallback to Azure OpenAI

## System Architecture
The project employs a clean architecture with a modular design for scalability and maintainability.

### Backend Architecture
-   **Framework:** FastAPI (Python 3.11).
-   **Core Layers:** Orchestration (parser, enricher, prompt builder, agent workflow), Enhanced GitHub Extractor, Interfaces (API, webhooks, bot), Features (business logic), Shared utilities, Data management, and Observability (Prometheus, OpenTelemetry).
-   **Database:** SQLAlchemy ORM supporting SQLite (default) and PostgreSQL with a repository pattern.
-   **AI Integration:** Factory pattern for pluggable LLM providers (Together AI, Azure OpenAI) with automatic fallback.
-   **Service Architecture:** Modular, LLM-powered service layer with `BaseService`, `ServiceManager`, and `ServiceLLMWrapper` for intelligent interactions across integrations like GitHub, Confluence, and MongoDB.
-   **Integration Wrappers:** Unified wrapper pattern for all external services (GitHub, Jira, Confluence) that uses ENV config by default and automatically falls back to Replit connectors. Makes integrations easily removable and switchable without changing business logic.
-   **Orchestration Layer:** Modular pipeline for message processing including `Message Parser` (with intelligent GitHub repository detection), `Context Enricher` (with caching), `Prompt Builder` (with templates), and a `LangGraph Agent` for task execution. Provides a unified facade for the pipeline and extensive structured logging.
-   **Intelligent Repository Matching:** Advanced fuzzy matching system that automatically resolves partial repository names to full paths. Supports compound word matching (e.g., "marketdata", "market data", "market-data" all match "am-market-data"), auto-loads repositories from GitHub organizations, and provides high-confidence matches using normalized similarity scoring.
-   **Logging:** Comprehensive structured logging with correlation IDs, method tracking, timing metrics, cache hit rates, and task execution status.

### Frontend Architecture
-   **Framework:** React 18 with TypeScript, built using Vite 5.
-   **Styling:** Tailwind CSS 3 with a modern vertical component architecture.
-   **UI/UX:** ChatGPT-like interface for LLM interaction, professional panels for integrations, and a "Thinking Mode."
-   **Chat History:** Full conversation management with SQLite/PostgreSQL storage, sidebar navigation, and auto-save.
-   **Voice Features:** Browser-native Web Speech API for speech-to-text and text-to-speech, with a dedicated animated Voice Assistant Panel.
-   **Navigation:** Streamlined 4-tab interface: Voice Assistant, LLM Testing, Integrations Hub, and Doc Orchestrator.
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
-   **Automated Workflows:** End-to-end processes for context enrichment, root cause analysis, code fix generation, pull request creation, and command-driven documentation orchestration.
-   **Real-time Backend Activity Streaming:** Live visualization of orchestration pipeline execution via Server-Sent Events (SSE) with a `StreamingOrchestrationWrapper` and a `BackendActivityStream` React component.
-   **Thinking Process Visualization:** Shared backend component for tracking workflow steps, displayed via a reusable frontend `ThinkingProcess` component.
-   **GitHub Context Detection:** Advanced repository reference parser with fuzzy matching. Automatically detects repository mentions in natural language (e.g., "repo marketdata"), normalizes variants (one word, hyphenated, spaced), and resolves to full repository paths using intelligent compound word matching with 85% confidence scoring.
-   **Documentation Orchestrator:** Automated workflow for creating branches, committing documentation to GitHub, publishing to Confluence, and creating Jira tickets, with clickable links to all generated artifacts.
-   **Observability:** Prometheus metrics, OpenTelemetry tracing, and comprehensive structured logging including request correlation IDs, LLM interaction logging, and timing information.

## External Dependencies
-   **AI Providers:** Together AI, Azure OpenAI
-   **Version Control:** GitHub
-   **Issue Tracking:** Jira
-   **Documentation:** Confluence
-   **Monitoring:** Grafana, Prometheus, OpenTelemetry
-   **Communication:** Microsoft Teams
-   **Database:** SQLAlchemy (for SQLite and PostgreSQL)
-   **Frontend Libraries:** React, Vite, Tailwind CSS, Lucide React, Axios
-   **Browser APIs:** Web Speech Recognition API, Web Speech Synthesis API