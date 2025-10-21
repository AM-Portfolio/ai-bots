# Setup & Configuration

Everything you need to get the AI Bots platform up and running.

## 📋 Setup Documentation

### [QUICK_START.md](./QUICK_START.md) 🚀
**Start here!** Quick setup guide to get running in minutes.

### [CONFIGURATION_GUIDE.md](./CONFIGURATION_GUIDE.md) ⚙️
Comprehensive configuration guide covering:
- Environment variables
- Service integrations
- Advanced settings

### [CONFIGURATION.md](./CONFIGURATION.md) 📝
Basic configuration reference and settings overview.

### [ACCESS_GUIDE.md](./ACCESS_GUIDE.md) 🔐
Access control, permissions, and authentication setup.

## 🎯 Setup Flow

1. **[Quick Start](./QUICK_START.md)** - Basic setup and first run
2. **[Configuration](./CONFIGURATION_GUIDE.md)** - Configure services
3. **[Access Setup](./ACCESS_GUIDE.md)** - Set up authentication
4. **[Test Connections](../../test_connections.py)** - Verify all services

## 🔧 Service Configuration

### Required Services
- **GitHub** - Repository access and PR creation
- **LLM Provider** - Together AI (default) or Azure OpenAI

### Optional Services
- **Confluence** - Documentation publishing
- **Jira** - Issue tracking integration
- **Azure Key Vault** - Secret management
- **Vector Database** - Qdrant for semantic search

## 🚀 Quick Test
```bash
# Test all connections after setup
python test_connections.py
```

## 📚 Related Documentation
- [API Documentation](../api/) - API configuration
- [Features](../features/) - Feature-specific setup
- [Testing](../testing/) - Setup verification