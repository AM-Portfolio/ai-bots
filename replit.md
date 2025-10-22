# AI Development Agent

## Overview
This project is an intelligent, autonomous development agent designed to automate and streamline the software development lifecycle. It analyzes bugs, diagnoses issues, generates fixes, and manages documentation across platforms by integrating with services like GitHub, Jira, Grafana, and Confluence. Leveraging AI for analysis, code generation, and documentation, the agent provides an end-to-end solution for automated bug resolution and documentation publishing through various interfaces including a React-based frontend with voice interaction. The project aims to significantly enhance developer productivity and system reliability with features like multi-source integration, AI-powered analysis, resilient LLM orchestration, and comprehensive Azure AI integration.

## User Preferences
- **Configuration Method**: ENV variables preferred over Replit connectors
- **LLM Provider**: Azure OpenAI as default primary provider with automatic fallback to Together AI and OpenAI. Role-based provider assignment (chat_provider, embedding_provider, beautify_provider) allows granular control.
- **Multilingual Support**: Automatic Hindi/English language detection enabled with language-aware responses
- **Vector Database**: Qdrant (persistent) preferred over in-memory for production use
- **UI Design**: Compact, space-efficient layouts with inline controls

## System Architecture
The project employs a clean architecture with a modular design for scalability and maintainability.

### Cloud-Agnostic Orchestration Layer
A template-based provider abstraction enables seamless switching between cloud providers (Azure, Together AI, OpenAI) using a factory pattern for instance creation and intelligent fallback chains. A unified API (`/api/ai/*`) supports runtime provider selection.

### Backend Architecture
Built with FastAPI (Python 3.11), the backend features a modular orchestration layer (parser, enricher, prompt builder, agent workflow), an enhanced GitHub extractor, and a repository pattern for SQLAlchemy (SQLite/PostgreSQL). It integrates a factory pattern for pluggable LLM providers with automatic fallback, comprehensive Azure AI Services (Speech, Translation, OpenAI models), and Qdrant as the primary vector database with automatic fallback to in-memory. A modular, LLM-powered service layer manages integrations (GitHub, Confluence, MongoDB) using unified integration wrappers. An intelligent repository matching system resolves partial repository names, and comprehensive structured logging is implemented.

### Frontend Architecture
The frontend uses React 18 with TypeScript and Vite 5, styled with Tailwind CSS 3 for compact, space-efficient layouts. It provides a ChatGPT-like interface for LLM interaction with inline settings, a full conversation management system, and an advanced cloud-based voice assistant leveraging OpenAI Whisper STT and TTS, featuring intent classification and continuous conversation. A streamlined 4-tab interface includes Voice Assistant, LLM Testing, Integrations Hub, and Doc Orchestrator. An Axios-based API client and a reactive activity logger provide robust functionality and observability.

### Key Features
Core features include multi-source integration (GitHub, Jira, Confluence, Grafana), AI-powered analysis (bug diagnosis, fix generation, documentation), resilient LLM orchestration with automatic fallback, comprehensive Azure AI integration for diverse workflows, and a resilient vector database (Qdrant with in-memory fallback). Automated workflows cover context enrichment, root cause analysis, code fix generation, and documentation orchestration. It also features real-time backend activity streaming, a thinking process visualization, advanced GitHub context detection with fuzzy matching, vector database-powered semantic search and code explanation, a specialized GitHub-LLM orchestrator with a 6-step workflow, and an automated response cleaner. Intelligent query detection routes specific requests, and an intelligent commit workflow, based on LangGraph, handles GitHub commits, PRs, and documentation publishing with UI approval. A complete voice assistant orchestration system manages sessions, intent classification, and voice-optimized responses. The documentation orchestrator automates publishing to GitHub, Confluence, and Jira. Observability is provided through Prometheus, OpenTelemetry, and structured logging.

## External Dependencies
-   **AI Providers:** Together AI, Azure OpenAI, OpenAI
-   **Version Control:** GitHub
-   **Issue Tracking:** Jira
-   **Documentation:** Confluence
-   **Monitoring:** Grafana, Prometheus, OpenTelemetry
-   **Communication:** Microsoft Teams
-   **Database:** SQLAlchemy (SQLite, PostgreSQL)
-   **Frontend Libraries:** React, Vite, Tailwind CSS, Lucide React, Axios
-   **Browser APIs:** MediaRecorder API, Web Speech Synthesis API