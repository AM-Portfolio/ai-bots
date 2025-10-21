# 📚 Documentation Quick Navigation

## 🚀 **Getting Started**
- **[📖 Main Documentation](./docs/README.md)** - Documentation hub
- **[⚡ Quick Start Guide](./docs/setup/QUICK_START.md)** - Get running fast
- **[⚙️ Configuration Guide](./docs/setup/CONFIGURATION_GUIDE.md)** - Complete setup

## 🔧 **Essential Links**
- **[🔌 API Reference](./docs/api/API_ENDPOINTS.md)** - Complete API docs
- **[🧪 Test Connections](./test_connections.py)** - Verify service connections
- **[🏗️ Architecture](./docs/ARCHITECTURE.md)** - System overview

## 📁 **Documentation Categories**

| Category | Description | Key Files |
|----------|-------------|-----------|
| **[🛠️ Setup](./docs/setup/)** | Installation & configuration | [Quick Start](./docs/setup/QUICK_START.md), [Config Guide](./docs/setup/CONFIGURATION_GUIDE.md) |
| **[🎯 Features](./docs/features/)** | Feature documentation | [AI Models](./docs/features/FEATURE_TOGETHER_AI_MODELS.md), [Voice](./docs/features/VOICE_ASSISTANT_GUIDE.md) |
| **[🔌 API](./docs/api/)** | API reference | [Endpoints](./docs/api/API_ENDPOINTS.md) |
| **[🚀 Deployment](./docs/deployment/)** | Deployment guides | [Deploy Guide](./docs/deployment/DEPLOYMENT_GUIDE.md), [Fixes](./docs/deployment/DEPLOYMENT_FIXES.md) |
| **[🧪 Testing](./docs/testing/)** | Testing procedures | [Quick Tests](./docs/testing/QUICK_TEST_STEPS.md), [UI Testing](./docs/testing/UI_TESTING_GUIDE.md) |
| **[📚 Guides](./docs/guides/)** | User guides | [LLM Guide](./docs/guides/LLM_PROVIDER_GUIDE.md), [Vector DB](./docs/guides/VECTOR_DB_QUICKSTART.md) |

## 🚀 **Quick Commands**

```bash
# Test all service connections
python test_connections.py

# Test specific service
python test_connections.py confluence

# Start application
python main.py

# View documentation structure
tree /f docs
```

## 📊 **Service Status Check**

```bash
# Check all services
python test_connections.py

# Individual service tests
python test_connections.py azure      # Azure services
python test_connections.py together   # Together AI
python test_connections.py github     # GitHub integration  
python test_connections.py confluence # Confluence
python test_connections.py jira       # Jira integration
python test_connections.py vector     # Vector database
```

---
**📖 For complete documentation, visit [./docs/README.md](./docs/README.md)**