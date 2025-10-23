# Project Organization

This document describes the organized structure of the AI Bots project.

## 📁 Directory Structure

### Core Directories

- **`code-intelligence/`** - Code embedding, semantic search, and analysis
- **`db/`** - Database models and repositories
- **`features/`** - Independent business capabilities (vertical slices)
- **`frontend/`** - React + Vite frontend application
- **`interfaces/`** - API endpoints and external adapters
- **`observability/`** - Logging, metrics, and monitoring
- **`orchestration/`** - LLM orchestration and workflows
- **`shared/`** - Shared utilities, config, and clients
- **`ui/`** - UI components and assets
- **`vector_db/`** - Vector database providers

### Organized Directories

- **`docker/`** - All Docker-related files
  - `Dockerfile` - Backend container
  - `Dockerfile.frontend` - Frontend container
  - `docker-compose.yml` - Full stack
  - `docker-compose.databases.yml` - Databases only
  - `docker-compose.app.yml` - Application only
  - `README.md` - Complete Docker documentation
  - `.dockerignore` - Build exclusions

- **`scripts/`** - Utility scripts
  - `start-app.ps1` - Windows backend startup
  - `start-full-app.ps1` - Windows full stack
  - `start-full-app.sh` - Linux/Mac full stack
  - `code-intel.ps1` - Windows code intelligence tools
  - `code-intel.sh` - Linux/Mac code intelligence tools

- **`tests/`** - All test files
  - `test_azure_config.py`
  - `test_chat_completion_config.py`
  - `test_connections.py`
  - `test_embedding_config.py`
  - `test_embeddings.py`
  - `test_llm_provider_auto_detection.py`
  - `test_provider_selection.py`

- **`archive/`** - Old files and test results
  - `connection_test_results_*.json`

- **`docs/`** - Documentation files
  - Architecture diagrams
  - API documentation
  - Guides and tutorials

- **`deps/`** - Python wheel dependencies (for offline installation)

- **`attached_assets/`** - Temporary/attached files

### Root Files

Essential configuration and entry points remain in root:

- **`main.py`** - Application entry point
- **`requirements.txt`** - Python dependencies
- **`package.json`** - Node.js dependencies
- **`.env`** - Local environment variables
- **`.env.docker`** - Docker environment variables
- **`docker-compose.yml`** - Main Docker compose (for convenience)
- **`docker-compose.databases.yml`** - Database compose (for convenience)
- **`docker-compose.app.yml`** - Application compose (for convenience)
- **`README.md`** - Main project documentation
- **`ARCHITECTURE_VECTOR_DB.md`** - Vector DB architecture
- **`DOCUMENTATION_ORGANIZATION.md`** - Documentation structure
- **`.gitignore`** - Git ignore rules

## 🎯 Benefits of This Organization

1. **Clear Separation** - Docker, scripts, tests each have their own directory
2. **Easy Discovery** - Related files are grouped together
3. **Clean Root** - Root directory only contains essential files
4. **Better Navigation** - Logical grouping makes files easier to find
5. **Maintainability** - Clear structure makes the project easier to maintain

## 🚀 Quick Access

### Running Services

```bash
# Using Docker (recommended)
docker-compose up -d --build

# Using scripts
.\scripts\start-full-app.ps1      # Windows
./scripts/start-full-app.sh       # Linux/Mac
```

### Running Tests

```bash
pytest tests/
```

### Docker Operations

All Docker files are in `docker/` directory. See `docker/README.md` for details.

## 📝 Migration Notes

The following files were moved to organize the project:

- **Moved to `docker/`**: Dockerfile, Dockerfile.frontend, DOCKER_README.md, .dockerignore
- **Moved to `scripts/`**: start-app.ps1, start-full-app.ps1, start-full-app.sh, code-intel.ps1, code-intel.sh
- **Moved to `tests/`**: All test_*.py files
- **Moved to `archive/`**: connection_test_results_*.json

All docker-compose files are available in both root (for convenience) and `docker/` directory (for organization).
