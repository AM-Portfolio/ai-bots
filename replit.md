# AI Development Agent - Replit Project

## Project Overview

This is an intelligent, autonomous development agent built in Python that:
- Analyzes bugs from multiple sources (GitHub, Jira, Grafana)
- Uses Azure OpenAI to diagnose issues and generate fixes
- Automatically creates pull requests with tests
- Publishes documentation to Confluence
- Provides REST API, webhooks, and Teams bot interfaces

## Technology Stack

- **Framework:** FastAPI
- **Database:** SQLAlchemy (SQLite default, PostgreSQL supported)
- **AI:** Together AI (default), Azure OpenAI (alternative) - Factory pattern
- **Integrations:** GitHub, Jira, Confluence, Grafana, Microsoft Teams
- **Monitoring:** Prometheus metrics, OpenTelemetry tracing
- **Language:** Python 3.11

## Architecture

The project follows a clean architecture with:

1. **Interfaces Layer** (`interfaces/`): API, webhooks, bot handlers
2. **Features Layer** (`features/`): Independent business capabilities
   - Context resolution
   - Issue analysis
   - Code generation
   - Test orchestration
   - Documentation publishing
   - Data injection
3. **Shared Layer** (`shared/`): Common utilities and clients
4. **Data Layer** (`db/`): Database models and repositories
5. **Observability** (`observability/`): Metrics and tracing

## Key Features Implemented

### ✅ Multi-Source Integration
- GitHub API client with issue/PR management
- Jira API client for ticket management
- Confluence client for documentation
- Grafana client for metrics/alerts

### ✅ AI-Powered Analysis
- Multi-provider LLM support (Together AI default, Azure OpenAI alternative)
- Factory pattern for easy provider switching
- Automated bug diagnosis
- Fix generation with explanations
- Test code generation
- Automatic fallback between providers

### ✅ Automated Workflows
- Context enrichment from multiple sources
- Root cause analysis
- Code fix generation
- Pull request creation
- Documentation publishing

### ✅ Observability
- Prometheus metrics export
- OpenTelemetry tracing support
- Structured logging

### ✅ Database
- SQLAlchemy ORM with Issue, Analysis, Fix models
- Repository pattern for data access
- Automatic schema creation

## Running the Project

The application is already configured to run automatically in Replit on port 5000.

**Manual start:**
```bash
python main.py
```

**Access the API:**
- Local: http://0.0.0.0:5000
- Replit: Use the provided webview URL

## Configuration Required

Before full functionality, configure these services in `.env`:

### Required for Core Features (LLM - Choose One):

**Option 1: Together AI (Recommended - Default)**
- `TOGETHER_API_KEY` - For AI analysis
- `TOGETHER_MODEL` - Model selection (optional, defaults to Llama-3.3-70B)

**Option 2: Azure OpenAI (Alternative)**
- `AZURE_OPENAI_ENDPOINT` - For AI analysis
- `AZURE_OPENAI_API_KEY` - For AI analysis

**Both (For Automatic Fallback)**
- Configure both providers for maximum reliability

### Optional Integrations:
- `GITHUB_TOKEN` - For GitHub integration
- `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` - For Jira
- `CONFLUENCE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` - For docs
- `GRAFANA_URL`, `GRAFANA_API_KEY` - For metrics
- `MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` - For Teams bot

See `.env.example` and `CONFIGURATION.md` for detailed setup.

## Project Structure

```
ai_dev_agent/
├── shared/              # Core utilities
│   ├── config.py        # Settings management
│   ├── models.py        # Pydantic models
│   ├── secrets.py       # Azure Key Vault
│   ├── llm.py          # OpenAI client
│   └── clients/        # External API clients
├── features/           # Business logic
│   ├── context_resolver/
│   ├── issue_analyzer/
│   ├── code_generator/
│   ├── test_orchestrator/
│   ├── doc_publisher/
│   └── data_injector/
├── interfaces/         # External interfaces
│   ├── http_api.py    # FastAPI app
│   └── teams_bot.py   # Teams bot
├── db/                # Database
│   ├── models.py      # ORM models
│   └── repo.py        # Repositories
├── observability/     # Monitoring
│   ├── metrics.py     # Prometheus
│   └── tracing.py     # OpenTelemetry
└── main.py           # Entry point
```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `POST /api/analyze` - Analyze issue
- `POST /api/webhook/{source}` - Receive webhooks
- `GET /metrics` - Prometheus metrics

See `API_ENDPOINTS.md` for complete documentation.

## Development Notes

### Database
- Default: SQLite (`ai_dev_agent.db`)
- Schema auto-created on startup
- For production: Use PostgreSQL via `DATABASE_URL`

### Hot Reload
- Enabled in development mode
- Changes auto-reload the server

### Logging
- Level: Configurable via `LOG_LEVEL` env var
- Default: INFO
- Format: Timestamp, logger name, level, message

## Recent Changes

**2025-10-17 (Latest):**
- ✅ Created comprehensive Streamlit testing UI in `ui/` package
- ✅ Added 8 test endpoints for individual feature testing
- ✅ Implemented dual workflow setup: API (port 5000) + UI (port 8501)
- ✅ Built UI-API integration layer with automatic URL detection
- ✅ Added comprehensive UI Testing Guide documentation
- ✅ All features now testable through intuitive web interface

**2025-10-17 (Earlier):**
- ✅ Integrated Together AI as default LLM provider
- ✅ Implemented factory pattern for multi-provider support
- ✅ Added automatic fallback (Together AI → Azure OpenAI)
- ✅ Updated all documentation for new provider architecture
- ✅ Created comprehensive LLM Provider Guide

**2025-10-16:**
- Complete project implementation
- All features operational
- Documentation created
- Server running successfully

## Known Limitations

1. **No Authentication:** API endpoints are open (implement for production)
2. **No Rate Limiting:** Should be added for production use
3. **Webhook Signatures:** Not validated (security concern)
4. **Error Handling:** Basic implementation, needs enhancement
5. **Testing:** No unit tests yet (should be added)

## Next Steps

1. Add authentication/authorization
2. Implement webhook signature validation
3. Add rate limiting
4. Write unit tests
5. Add integration tests
6. Enhance error handling
7. Add caching layer (Redis)
8. Implement async task queue
9. Add more sophisticated AI prompts
10. Build admin dashboard

## User Preferences

None specified yet - will be updated as preferences are communicated.

## Useful Commands

**Start server:**
```bash
python main.py
```

**Start testing UI:**
```bash
cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**Test health:**
```bash
curl http://localhost:5000/health
```

**View metrics:**
```bash
curl http://localhost:5000/metrics
```

**Test analysis:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"issue_id": "123", "source": "github", "repository": "owner/repo"}'
```

**Test individual features:**
```bash
# Test LLM
curl -X POST "http://localhost:5000/api/test/llm?prompt=Hello&provider=together"

# Test GitHub
curl -X POST "http://localhost:5000/api/test/github?repository=owner/repo"
```

## Support Documentation

- `README.md` - Project overview and quick start
- `ACCESS_GUIDE.md` - **How to access API and UI (START HERE!)**
- `CONFIGURATION.md` - Complete setup guide for all integrations
- `API_ENDPOINTS.md` - Detailed API documentation
- `UI_TESTING_GUIDE.md` - Comprehensive UI testing guide
- `LLM_PROVIDER_GUIDE.md` - LLM provider setup and usage
- `.env.example` - Environment variables template

## Project Status

**Status:** ✅ Operational

The AI Development Agent is fully implemented and running. All core features are functional, though external integrations require proper API credentials to work fully.
