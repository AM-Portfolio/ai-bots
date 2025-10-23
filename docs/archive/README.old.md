# AI Bots Documentation

Welcome to the AI Bots project documentation! This directory contains comprehensive documentation organized by category.

## 📁 Documentation Structure

### 🔌 [API Documentation](./api/)
- **[API_ENDPOINTS.md](./api/API_ENDPOINTS.md)** - Complete API reference and endpoints documentation

### ⚙️ [Setup & Configuration](./setup/)
- **[QUICK_START.md](./setup/QUICK_START.md)** - Quick start guide to get up and running
- **[CONFIGURATION.md](./setup/CONFIGURATION.md)** - Basic configuration settings
- **[CONFIGURATION_GUIDE.md](./setup/CONFIGURATION_GUIDE.md)** - Detailed configuration guide
- **[ACCESS_GUIDE.md](./setup/ACCESS_GUIDE.md)** - Access control and permissions guide

### 🎯 [Features](./features/)
- **[FEATURE_CONVERSATIONAL_CONTEXT.md](./features/FEATURE_CONVERSATIONAL_CONTEXT.md)** - Conversational context management
- **[FEATURE_TOGETHER_AI_MODELS.md](./features/FEATURE_TOGETHER_AI_MODELS.md)** - Together AI models integration
- **[VOICE_ASSISTANT_GUIDE.md](./features/VOICE_ASSISTANT_GUIDE.md)** - Voice assistant functionality
- **[VOICE_FEATURES_GUIDE.md](./features/VOICE_FEATURES_GUIDE.md)** - Voice features overview
- **[MESSAGE_PARSER_IMPROVEMENTS.md](./features/MESSAGE_PARSER_IMPROVEMENTS.md)** - Message parsing enhancements

### 🚀 [Deployment](./deployment/)
- **[DEPLOYMENT_GUIDE.md](./deployment/DEPLOYMENT_GUIDE.md)** - Step-by-step deployment guide
- **[DEPLOYMENT_SUMMARY.md](./deployment/DEPLOYMENT_SUMMARY.md)** - Deployment overview and summary
- **[DEPLOYMENT_FIXES.md](./deployment/DEPLOYMENT_FIXES.md)** - Common deployment issues and fixes

### 🧪 [Testing](./testing/)
- **[UI_TESTING_GUIDE.md](./testing/UI_TESTING_GUIDE.md)** - UI testing procedures
- **[TOGETHER_AI_TESTING_GUIDE.md](./testing/TOGETHER_AI_TESTING_GUIDE.md)** - Together AI testing guide
- **[QUICK_TEST_STEPS.md](./testing/QUICK_TEST_STEPS.md)** - Quick testing steps and procedures

### 📚 [User Guides](./guides/)
- **[LLM_PROVIDER_GUIDE.md](./guides/LLM_PROVIDER_GUIDE.md)** - LLM provider configuration and usage
- **[LOGGING_GUIDE.md](./guides/LOGGING_GUIDE.md)** - Logging configuration and best practices
- **[VECTOR_DB_QUICKSTART.md](./guides/VECTOR_DB_QUICKSTART.md)** - Vector database quick start
- **[VECTOR_DB_USAGE.md](./guides/VECTOR_DB_USAGE.md)** - Vector database usage guide
- **[QDRANT_REPOSITORY_INDEXING.md](./guides/QDRANT_REPOSITORY_INDEXING.md)** - Qdrant repository indexing

### 🏗️ Architecture & Design
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture overview
- **[PROJECT_COMPLETE.md](./PROJECT_COMPLETE.md)** - Project completion status and overview

## 🚀 Quick Navigation

### New Users
1. Start with [Quick Start Guide](./setup/QUICK_START.md)
2. Review [Configuration Guide](./setup/CONFIGURATION_GUIDE.md)
3. Check [API Documentation](./api/API_ENDPOINTS.md)

### Developers
1. Read [Architecture](./ARCHITECTURE.md)
2. Review [Features](./features/)
3. Check [Testing Guides](./testing/)

### DevOps/Deployment
1. Follow [Deployment Guide](./deployment/DEPLOYMENT_GUIDE.md)
2. Review [Deployment Fixes](./deployment/DEPLOYMENT_FIXES.md)
3. Check [Configuration](./setup/)

### Feature Development
1. Review existing [Features](./features/)
2. Check [Testing Procedures](./testing/)
3. Update relevant documentation

## 🔧 Service Connections

The project includes comprehensive connection testing for all services:

```bash
# Test all service connections
python test_connections.py

# Test specific service
python test_connections.py confluence
python test_connections.py jira
python test_connections.py github
python test_connections.py azure
python test_connections.py together
python test_connections.py vector
```

## 📖 Documentation Guidelines

When adding new documentation:

1. **Place in appropriate category folder**
2. **Use clear, descriptive filenames**
3. **Add entry to this README**
4. **Include proper markdown formatting**
5. **Add relevant tags and categories**

## 🤝 Contributing

- Documentation follows markdown standards
- Include code examples where applicable
- Keep documentation up-to-date with code changes
- Use consistent formatting and structure

---

**Need help?** Check the [Quick Start Guide](./setup/QUICK_START.md) or [Configuration Guide](./setup/CONFIGURATION_GUIDE.md).