# AI Development Agent

## Overview
This project is an intelligent, autonomous development agent written in Python. Its primary purpose is to automate and streamline the software development lifecycle by analyzing bugs, diagnosing issues, generating fixes, and managing documentation across various platforms. The agent integrates with multiple services like GitHub, Jira, Grafana, and Confluence, leveraging AI for analysis, code generation, and documentation. It offers REST API, webhooks, and a Microsoft Teams bot interface, along with a modern React-based frontend with voice interaction capabilities. The project aims to provide an end-to-end solution for automated bug resolution and documentation publishing.

## User Preferences
None specified yet - will be updated as preferences are communicated.

## System Architecture
The project employs a clean architecture approach, separating concerns into distinct layers for maintainability and scalability.

### Backend Architecture
-   **Framework:** FastAPI (Python 3.11)
-   **Core Layers:**
    -   **Interfaces:** Handles external communication (API, webhooks, bot, service management API).
    -   **Features:** Encapsulates independent business logic (e.g., context resolution, issue analysis, code generation, test orchestration, documentation publishing).
    -   **Shared:** Provides common utilities, clients, and unified service architecture.
    -   **Data:** Manages database interactions and models.
    -   **Observability:** Implements monitoring with Prometheus metrics and OpenTelemetry tracing.
-   **Database:** SQLAlchemy ORM supporting SQLite (default) and PostgreSQL, using a repository pattern.
-   **AI Integration:** Utilizes a factory pattern for pluggable LLM providers (Together AI, Azure OpenAI) with automatic fallback.
-   **Service Architecture (New):** Modular, LLM-powered service layer with:
    -   **BaseService:** Abstract base class for all integrations (~85 lines)
    -   **ServiceManager:** Connection pooling, lifecycle management, LLM-enhanced execution (~145 lines)
    -   **ServiceLLMWrapper:** AI-powered query enhancement, response interpretation, error analysis (~135 lines)
    -   **Service Implementations:** GitHub (~240 lines), Confluence (~195 lines), MongoDB (~220 lines)
    -   **Benefits:** Each service file <250 lines, LLM wrapper for intelligent interactions, extensible for future services
    -   **Total Architecture:** ~991 lines across all service files (vs 471 lines for old GitHub client alone)

### Frontend Architecture
-   **Framework:** React 18 with TypeScript.
-   **Build Tool:** Vite 5.
-   **Styling:** Tailwind CSS 3, featuring a modern vertical component architecture.
-   **UI/UX:** Designed with a ChatGPT-like interface for LLM interaction, professional panels for integrations and workflows, and a clean "Thinking Mode" for focused interaction.
-   **Chat History:** Full conversation management with SQLite/PostgreSQL storage, sidebar navigation, auto-save functionality, and conversation persistence across sessions.
-   **Voice Features:** Integrates browser-native Web Speech API for both speech-to-text input and text-to-speech output, providing voice assistance without external API keys.
-   **Voice Assistant Panel:** Dedicated animated UI with auto-greeting, continuous voice conversation, circular voice visualization with pulsing animations, and real-time visual feedback for listening/speaking states.
-   **Navigation:** Streamlined 4-tab interface - Voice Assistant, LLM Testing, Integrations Hub (unified integrations & configuration), and Doc Orchestrator.
-   **Components:** Organized into Layout (Sidebar, Header) and Panels (VoiceAssistantPanel, LLMTestPanel, IntegrationsHub, DocOrchestratorPanel).
-   **Integrations Hub:** Unified, extensible integration management system with:
    -   Category-based organization (Version Control, Issue Tracking, Knowledge Base, Monitoring, Databases, APIs, Cloud, AI Providers)
    -   Service registry with declarative configuration schema
    -   Visual service cards with status indicators (connected/disconnected/error/testing)
    -   Modal drawer for configuration with form validation
    -   Built-in test connection functionality
    -   Support for multiple auth types (basic, token, OAuth, API key, connection string)
    -   Pre-configured services: GitHub, Jira, Confluence, Grafana, PostgreSQL, MongoDB, OpenAI, Azure, Stripe, Twilio, SendGrid, REST API
    -   Extensible architecture for adding new services with minimal code
-   **Compact Settings:** Modern settings bar positioned below chat input with model selector, voice toggle, and backend details in a single streamlined row.
-   **Doc Orchestrator UI:** User-friendly checkbox-based interface allowing selective publishing to GitHub, Confluence, and/or Jira with expandable configuration fields and visual service icons.
-   **API Client:** Axios-based HTTP client with strong TypeScript typing for API responses.

### Deployment
-   Configured for Autoscale deployment on Replit.
-   The FastAPI backend serves both API endpoints and the pre-built React frontend (static files from `frontend/dist/`), handling SPA routing.

### Key Features
-   **Multi-Source Integration:** Connectors for GitHub, Jira, Confluence (Basic Auth with API tokens), and Grafana.
-   **AI-Powered Analysis:** Automated bug diagnosis, fix generation, test code generation, and documentation generation using LLMs.
-   **Automated Workflows:** End-to-end processes for context enrichment, root cause analysis, code fix generation, pull request creation, and command-driven documentation orchestration (analysis → generation → commit → publish → ticket).
-   **Thinking Process Visualization:** Shared backend component that tracks workflow execution steps with status, metadata, and timing. Displayed via reusable frontend ThinkingProcess component in both LLM Testing and Doc Orchestrator panels. Provides real-time visibility into backend processing flow.
-   **GitHub Context Detection:** LLM automatically detects GitHub repository mentions in prompts and enriches context with repository information.
-   **Documentation Orchestrator:** Automated workflow that creates a new branch, commits documentation to GitHub, publishes to Confluence, and creates Jira tickets. Provides clickable links to GitHub files (with branch name), Confluence pages, commit URLs, and Jira tickets for easy access to all generated artifacts.
-   **Observability:** Prometheus metrics, OpenTelemetry tracing, and comprehensive structured logging with:
    -   Request correlation IDs for tracing across services
    -   LLM interaction logging with request/response metrics
    -   Timing information for all operations
    -   JSON-structured metadata for easy parsing
    -   Method entry/exit tracking with decorators
    -   API request/response logging middleware

## External Dependencies
-   **AI Providers:** Together AI (default), Azure OpenAI (alternative)
-   **Version Control:** GitHub
-   **Issue Tracking:** Jira
-   **Documentation:** Confluence
-   **Monitoring:** Grafana, Prometheus, OpenTelemetry
-   **Communication:** Microsoft Teams
-   **Database:** SQLAlchemy (for SQLite and PostgreSQL)
-   **Frontend Libraries:** React, Vite, Tailwind CSS, Lucide React, Axios
-   **Browser APIs:** Web Speech Recognition API, Web Speech Synthesis API