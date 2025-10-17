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
    -   **Interfaces:** Handles external communication (API, webhooks, bot).
    -   **Features:** Encapsulates independent business logic (e.g., context resolution, issue analysis, code generation, test orchestration, documentation publishing).
    -   **Shared:** Provides common utilities and clients.
    -   **Data:** Manages database interactions and models.
    -   **Observability:** Implements monitoring with Prometheus metrics and OpenTelemetry tracing.
-   **Database:** SQLAlchemy ORM supporting SQLite (default) and PostgreSQL, using a repository pattern.
-   **AI Integration:** Utilizes a factory pattern for pluggable LLM providers (Together AI, Azure OpenAI) with automatic fallback.

### Frontend Architecture
-   **Framework:** React 18 with TypeScript.
-   **Build Tool:** Vite 5.
-   **Styling:** Tailwind CSS 3, featuring a modern vertical component architecture.
-   **UI/UX:** Designed with a ChatGPT-like interface for LLM interaction, professional panels for integrations and workflows, and a clean "Thinking Mode" for focused interaction.
-   **Voice Features:** Integrates browser-native Web Speech API for both speech-to-text input and text-to-speech output, providing voice assistance without external API keys.
-   **Voice Assistant Panel:** Dedicated animated UI with auto-greeting, continuous voice conversation, circular voice visualization with pulsing animations, and real-time visual feedback for listening/speaking states.
-   **Navigation:** Streamlined 5-tab interface - Voice Assistant, LLM Testing, Integrations (includes GitHub/Jira/Confluence/Grafana), Configuration, and Doc Orchestrator.
-   **Components:** Organized into Layout (Sidebar, Header) and Panels (VoiceAssistantPanel, LLMTestPanel, IntegrationsPanel, ConfigurationPanel, DocOrchestratorPanel).
-   **API Client:** Axios-based HTTP client with strong TypeScript typing for API responses.

### Deployment
-   Configured for Autoscale deployment on Replit.
-   The FastAPI backend serves both API endpoints and the pre-built React frontend (static files from `frontend/dist/`), handling SPA routing.

### Key Features
-   **Multi-Source Integration:** Connectors for GitHub, Jira, Confluence, and Grafana.
-   **AI-Powered Analysis:** Automated bug diagnosis, fix generation, test code generation, and documentation generation using LLMs.
-   **Automated Workflows:** End-to-end processes for context enrichment, root cause analysis, code fix generation, pull request creation, and command-driven documentation orchestration (analysis → generation → commit → publish → ticket).
-   **Observability:** Prometheus metrics, OpenTelemetry tracing, and structured logging.

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