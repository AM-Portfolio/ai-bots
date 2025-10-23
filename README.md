# AI Development Agent

An intelligent, autonomous development agent that diagnoses bugs, generates fixes, creates pull requests, and publishes documentation across multiple platforms.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d --build

# Access the application
# Frontend: http://localhost:4000
# Backend: http://localhost:9000
# API Docs: http://localhost:9000/docs
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# Start backend
python main.py

# Start frontend (in another terminal)
cd frontend && npm run dev
```

## 🌟 Features

- **Multi-Source Issue Resolution**: Analyze issues from GitHub, Jira, Grafana alerts
- **AI-Powered Code Analysis**: Uses Together AI (default) or Azure OpenAI to diagnose bugs and generate fixes
- **Multi-Provider LLM Support**: Factory pattern with Together AI (default) and Azure OpenAI
- **Code Intelligence**: Semantic code search and embedding with Qdrant
- **Automated Testing**: Generates unit tests for all code fixes
- **PR Creation**: Automatically creates pull requests with fixes
- **Documentation**: Auto-generates and publishes Confluence documentation
- **Observability**: Built-in metrics (Prometheus) and tracing (OpenTelemetry)
- **Multiple Interfaces**: REST API, Webhooks, and Microsoft Teams bot

## 📁 Project Structure

```
ai-bots/
│
├── archive/                    # Old test results and archived files
├── code-intelligence/          # Code embedding & semantic search
│   ├── analysis/               # Code analysis pipelines
│   ├── commands/               # CLI commands
│   ├── parsers/                # Language-specific parsers
│   ├── pipeline/               # Processing pipelines
│   ├── storage/                # Vector storage interfaces
│   └── tests/                  # Integration tests
│
├── db/                         # Database layer
│   ├── models.py               # SQLAlchemy ORM models
│   └── repo.py                 # Database repositories
│
├── docker/                     # 🐳 Docker configuration
│   ├── Dockerfile              # Backend container
│   ├── Dockerfile.frontend     # Frontend container
│   ├── docker-compose.yml      # Full stack
│   ├── docker-compose.databases.yml  # Databases only
│   ├── docker-compose.app.yml  # Application only
│   └── README.md               # Docker documentation
│
├── features/                   # 🧩 Independent vertical slices
│   ├── context_resolver/       # Enriches issues with context
│   ├── issue_analyzer/         # Diagnoses bugs using AI
│   ├── code_generator/         # Generates fixes and tests
│   ├── test_orchestrator/      # Creates PRs and triggers CI
│   ├── doc_publisher/          # Publishes to Confluence
│   └── data_injector/          # Pulls logs, metrics, tickets
│
├── frontend/                   # React + Vite frontend
│   ├── src/                    # Source code
│   └── nginx.conf              # Nginx configuration
│
├── interfaces/                 # External adapters
│   ├── teams_bot.py            # Microsoft Teams bot handler
│   └── http_api.py             # REST API and webhooks
│
├── observability/              # Logging & monitoring
│
├── orchestration/              # LLM orchestration & workflows
│   ├── github_llm/             # GitHub integration
│   └── resilient_orchestrator.py  # Multi-provider LLM
│
├── scripts/                    # 📜 Utility scripts
│   ├── start-app.ps1           # Windows startup
│   ├── start-full-app.ps1      # Full stack startup
│   ├── start-full-app.sh       # Linux startup
│   ├── code-intel.ps1          # Code intelligence tools
│   └── code-intel.sh           # Linux code intel
│
├── shared/                     # 🔑 Reusable core components
│   ├── config.py               # Application configuration
│   ├── models.py               # Global Pydantic models
│   ├── secrets.py              # Azure Key Vault integration
│   ├── llm.py                  # LLM client with factory pattern
│   ├── llm_providers/          # LLM provider implementations
│   │   ├── base.py             # Base provider interface
│   │   ├── together_provider.py # Together AI (default)
│   │   ├── azure_provider.py   # Azure OpenAI (alternative)
│   │   └── factory.py          # Provider factory
│   └── clients/                # External service clients
│       ├── github_client.py    # GitHub API integration
│       ├── jira_client.py      # Jira API integration
│       ├── confluence_client.py # Confluence API integration
│       └── grafana_client.py   # Grafana API integration
│
├── tests/                      # 🧪 Test files
│   ├── test_azure_config.py
│   ├── test_chat_completion_config.py
│   ├── test_connections.py
│   └── test_*.py
│
├── ui/                         # UI components & assets
│
├── vector_db/                  # Vector database providers
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables
│   └── repo.py                 # Data access repositories
│
├── observability/              # Telemetry
│   ├── metrics.py              # Prometheus metrics
│   └── tracing.py              # OpenTelemetry tracing
│
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── .env.example                # Environment variables template
```

## 🚀 Quick Start

### 📍 **Accessing in Replit (Already Running!)**

Both services are live and ready:

1. **Backend API** (Port 5000)
   - Click the **Webview** button or use Replit's provided URL
   - API docs: `https://[your-url].repl.co/docs`
   - Health check: `https://[your-url].repl.co/health`

2. **Testing UI** (Port 8501)
   - Access via port forwarding: `https://[your-url].repl.co:8501`
   - Test all features through web interface
   - No coding required!

📖 **See [ACCESS_GUIDE.md](ACCESS_GUIDE.md) for complete access instructions**

### 🚀 **Deploy to Production**

The app is configured to deploy **both API and Testing UI**:
- **Deployment Mode:** VM (supports multiple ports)
- **API URL:** `https://[your-app].repl.co`
- **UI URL:** `https://[your-app].repl.co:3000`

Click **Deploy/Publish** in Replit to make it live!

### 💻 **Local Setup**

#### 1. Installation

```bash
# Dependencies are pre-installed in Replit
# For local setup:
pip install -r requirements.txt
```

#### 2. Configuration

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed setup instructions.

## 📚 Documentation

Comprehensive documentation is organized in the [`docs/`](./docs/) directory:

### 🔗 Quick Links
- **[📖 Complete Documentation](./docs/README.md)** - Central documentation hub
- **[🚀 Quick Start Guide](./docs/setup/QUICK_START.md)** - Get up and running fast
- **[⚙️ Configuration Guide](./docs/setup/CONFIGURATION_GUIDE.md)** - Detailed configuration
- **[🔌 API Reference](./docs/api/API_ENDPOINTS.md)** - Complete API documentation

### 📁 Documentation Categories
- **[Setup & Configuration](./docs/setup/)** - Installation and configuration guides
- **[Features](./docs/features/)** - Feature-specific documentation  
- **[API](./docs/api/)** - API reference and endpoints
- **[Deployment](./docs/deployment/)** - Deployment guides and troubleshooting
- **[Testing](./docs/testing/)** - Testing procedures and guides
- **[User Guides](./docs/guides/)** - How-to guides and tutorials

### 🔧 Service Connection Testing
Test all integrated services with the built-in testing suite:

```bash
# Test all service connections
python test_connections.py

# Test specific services
python test_connections.py confluence  # Test Confluence connection
python test_connections.py jira       # Test Jira connection  
python test_connections.py github     # Test GitHub connection
python test_connections.py azure      # Test Azure services
python test_connections.py together   # Test Together AI
python test_connections.py vector     # Test vector database
```

#### 3. Run the Application

```bash
# Backend API
python main.py

# Testing UI (in separate terminal)
cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**URLs:**
- Backend API: `http://localhost:5000`
- Testing UI: `http://localhost:8501`

## 📡 API Endpoints

### Health Check
```http
GET /
GET /health
```

### Analyze Issue
```http
POST /api/analyze
Content-Type: application/json

{
  "issue_id": "123",
  "source": "github",
  "repository": "owner/repo",
  "create_pr": true,
  "publish_docs": false,
  "confluence_space": "DEV"
}
```

**Response:**
```json
{
  "issue_id": "123",
  "analysis": {
    "root_cause": "Null pointer exception in UserService",
    "confidence_score": 0.95,
    "suggested_fixes": [...]
  },
  "fixes_count": 1,
  "pr_url": "https://github.com/owner/repo/pull/456",
  "documentation_page": "12345"
}
```

### Webhooks

Receive automated events from external services:

```http
POST /api/webhook/github
POST /api/webhook/grafana
POST /api/webhook/jira
```

### Metrics

Prometheus-compatible metrics:

```http
GET /metrics
```

## 🔧 Integration Setup

### GitHub Integration
1. Create a Personal Access Token with `repo` scope
2. Set `GITHUB_TOKEN` in `.env`
3. Configure webhook URL: `https://your-app.com/api/webhook/github`

### Jira Integration
1. Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Set `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` in `.env`

### Azure OpenAI
1. Create an Azure OpenAI resource
2. Deploy a GPT-4 model
3. Set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` in `.env`

### Confluence
1. Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens
2. Set `CONFLUENCE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN` in `.env`

### Grafana
1. Create a service account token in Grafana
2. Set `GRAFANA_URL` and `GRAFANA_API_KEY` in `.env`

### Microsoft Teams Bot
1. Register bot in Azure Bot Service
2. Set `MICROSOFT_APP_ID` and `MICROSOFT_APP_PASSWORD` in `.env`

## 🤖 Teams Bot Commands

In Microsoft Teams, interact with the bot using:

- `analyze <source> <issue_id>` - Analyze an issue
  - Example: `analyze github 123`
- `status` - Check bot status
- `help` - Show available commands

## 🔐 Security

- Secrets managed via Azure Key Vault (optional)
- Environment variables for local development
- Never commit `.env` file to version control

## 📊 Monitoring

### Prometheus Metrics
- `ai_dev_agent_issues_analyzed_total` - Issues analyzed by source and severity
- `ai_dev_agent_fixes_generated_total` - Total fixes generated
- `ai_dev_agent_prs_created_total` - PRs created by repository
- `ai_dev_agent_analysis_duration_seconds` - Analysis time histogram
- `ai_dev_agent_llm_calls_total` - LLM API calls by operation

### Database
SQLite by default. For production, configure PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_dev_agent
```

## 🏗️ Architecture

The application follows a clean architecture pattern:

1. **Interfaces Layer**: API, webhooks, bot handlers
2. **Features Layer**: Independent business capabilities
3. **Shared Layer**: Common utilities and clients
4. **Data Layer**: Database models and repositories

## 🔄 Workflow Example

1. **Receive Issue**: Via webhook or API call
2. **Resolve Context**: Fetch related code, logs, metrics
3. **Analyze**: Use AI to diagnose root cause
4. **Generate Fix**: Create code fix with tests
5. **Test**: Create PR and trigger CI
6. **Document**: Publish analysis to Confluence

## 🛠️ Development

### Utility Scripts

The `scripts/` directory contains helpful utilities:

```bash
# Windows - Start backend
.\scripts\start-app.ps1

# Windows - Start full stack (backend + frontend)
.\scripts\start-full-app.ps1

# Linux/Mac - Start full stack
./scripts/start-full-app.sh

# Code intelligence tools
.\scripts\code-intel.ps1      # Windows
./scripts/code-intel.sh       # Linux/Mac
```

### Local Development
```bash
python main.py
```

The server runs with hot-reload enabled in development mode.

### Testing
```bash
pytest tests/
```

All test files are organized in the `tests/` directory.

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 🐳 Docker Deployment

All Docker-related files are in the `docker/` directory. See [docker/README.md](docker/README.md) for complete documentation.

```bash
# Start full stack
docker-compose up -d --build

# Start databases only
docker-compose -f docker/docker-compose.databases.yml up -d

# Start application only
docker-compose -f docker/docker-compose.app.yml up -d
```

## 📂 Directory Organization

- **`docker/`** - All Docker configuration files (Dockerfiles, compose files, docs)
- **`scripts/`** - Utility scripts for starting services and tools
- **`tests/`** - All test files and test utilities
- **`archive/`** - Old test results and archived files
- **Root directory** - Core application code and configuration

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Support

For issues and questions:
- Create an issue in the repository
- Contact the development team
