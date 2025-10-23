# 📚 AI-Bots Documentation# AI Bots Documentation



Welcome to the AI-Bots documentation. This guide will help you get started quickly and navigate through the features.Welcome to the AI Bots project documentation! This directory contains comprehensive documentation organized by category.



## 🚀 Quick Start## 📁 Documentation Structure



1. **Setup**: See [Setup Guide](setup/CONFIGURATION_GUIDE.md)### 🔌 [API Documentation](./api/)

2. **Configuration**: Edit `.env` file with your API keys- **[API_ENDPOINTS.md](./api/API_ENDPOINTS.md)** - Complete API reference and endpoints documentation

3. **Test Connection**: Run `python test_connections.py`

4. **Start Application**: Run `python main.py`### ⚙️ [Setup & Configuration](./setup/)

- **[QUICK_START.md](./setup/QUICK_START.md)** - Quick start guide to get up and running

```bash- **[CONFIGURATION.md](./setup/CONFIGURATION.md)** - Basic configuration settings

# Quick setup commands- **[CONFIGURATION_GUIDE.md](./setup/CONFIGURATION_GUIDE.md)** - Detailed configuration guide

cp .env.example .env  # Copy environment template- **[ACCESS_GUIDE.md](./setup/ACCESS_GUIDE.md)** - Access control and permissions guide

# Edit .env with your credentials

python test_connections.py  # Verify configuration### 🎯 [Features](./features/)

python main.py  # Start the application- **[FEATURE_CONVERSATIONAL_CONTEXT.md](./features/FEATURE_CONVERSATIONAL_CONTEXT.md)** - Conversational context management

```- **[FEATURE_TOGETHER_AI_MODELS.md](./features/FEATURE_TOGETHER_AI_MODELS.md)** - Together AI models integration

- **[VOICE_ASSISTANT_GUIDE.md](./features/VOICE_ASSISTANT_GUIDE.md)** - Voice assistant functionality

## 📖 Core Documentation- **[VOICE_FEATURES_GUIDE.md](./features/VOICE_FEATURES_GUIDE.md)** - Voice features overview

- **[MESSAGE_PARSER_IMPROVEMENTS.md](./features/MESSAGE_PARSER_IMPROVEMENTS.md)** - Message parsing enhancements

### Setup & Configuration

- **[Configuration Guide](setup/CONFIGURATION_GUIDE.md)** - Complete setup instructions### 🚀 [Deployment](./deployment/)

- **[Access Guide](setup/ACCESS_GUIDE.md)** - Quick access and getting started- **[DEPLOYMENT_GUIDE.md](./deployment/DEPLOYMENT_GUIDE.md)** - Step-by-step deployment guide

- **Environment Variables** - See `.env.example` for all settings- **[DEPLOYMENT_SUMMARY.md](./deployment/DEPLOYMENT_SUMMARY.md)** - Deployment overview and summary

- **[DEPLOYMENT_FIXES.md](./deployment/DEPLOYMENT_FIXES.md)** - Common deployment issues and fixes

### Features

- **[Code Intelligence](../code-intelligence/README.md)** - Repository embedding and analysis### 🧪 [Testing](./testing/)

  - [Quick Reference](../code-intelligence/QUICK_REFERENCE.md)- **[UI_TESTING_GUIDE.md](./testing/UI_TESTING_GUIDE.md)** - UI testing procedures

  - [Quick Start](../code-intelligence/QUICK_START.md)- **[TOGETHER_AI_TESTING_GUIDE.md](./testing/TOGETHER_AI_TESTING_GUIDE.md)** - Together AI testing guide

  - [Enhanced Features](../code-intelligence/ENHANCED_FEATURES.md)- **[QUICK_TEST_STEPS.md](./testing/QUICK_TEST_STEPS.md)** - Quick testing steps and procedures

  - [Tech Stack Support](../code-intelligence/TECH_STACK_SUPPORT.md)

- **Vector Database** - Semantic search and repository indexing### 📚 [User Guides](./guides/)

  - [Consolidation Summary](CONSOLIDATION_SUMMARY.md)- **[LLM_PROVIDER_GUIDE.md](./guides/LLM_PROVIDER_GUIDE.md)** - LLM provider configuration and usage

  - [Migration Guide](MIGRATION_GUIDE_REPOSITORY_INDEXING.md)- **[LOGGING_GUIDE.md](./guides/LOGGING_GUIDE.md)** - Logging configuration and best practices

- **[VECTOR_DB_QUICKSTART.md](./guides/VECTOR_DB_QUICKSTART.md)** - Vector database quick start

### Testing- **[VECTOR_DB_USAGE.md](./guides/VECTOR_DB_USAGE.md)** - Vector database usage guide

- **[Testing Guide](testing/README.md)** - How to test the application- **[QDRANT_REPOSITORY_INDEXING.md](./guides/QDRANT_REPOSITORY_INDEXING.md)** - Qdrant repository indexing

- **[Quick Test Steps](testing/QUICK_TEST_STEPS.md)** - Fast verification

- **[UI Testing](testing/UI_TESTING_GUIDE.md)** - Frontend testing guide### 🏗️ Architecture & Design

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System architecture overview

### Architecture- **[PROJECT_COMPLETE.md](./PROJECT_COMPLETE.md)** - Project completion status and overview

- **[Architecture Overview](ARCHITECTURE.md)** - System design and components

- **[Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md)** - Visual representations## 🚀 Quick Navigation

- **[API Documentation](api/README.md)** - API endpoints and usage

### New Users

### Deployment1. Start with [Quick Start Guide](./setup/QUICK_START.md)

- **[Deployment Guide](deployment/README.md)** - How to deploy2. Review [Configuration Guide](./setup/CONFIGURATION_GUIDE.md)

- **[Deployment Summary](deployment/DEPLOYMENT_SUMMARY.md)** - Deployment checklist3. Check [API Documentation](./api/API_ENDPOINTS.md)



## 🎯 Key Features### Developers

1. Read [Architecture](./ARCHITECTURE.md)

### 1. Code Intelligence2. Review [Features](./features/)

Advanced repository analysis with:3. Check [Testing Guides](./testing/)

- Tree-sitter semantic parsing

- Enhanced summarization### DevOps/Deployment

- Multi-language support (Python, JS/TS, Java, Kotlin, C/C++, Dart)1. Follow [Deployment Guide](./deployment/DEPLOYMENT_GUIDE.md)

- Incremental updates2. Review [Deployment Fixes](./deployment/DEPLOYMENT_FIXES.md)

- Smart file prioritization3. Check [Configuration](./setup/)



**Quick Start:**### Feature Development

```bash1. Review existing [Features](./features/)

cd code-intelligence2. Check [Testing Procedures](./testing/)

python orchestrator.py health  # Check connectivity3. Update relevant documentation

python orchestrator.py embed   # Embed repository

python orchestrator.py analyze # Analyze changes## 🔧 Service Connections

```

The project includes comprehensive connection testing for all services:

### 2. Vector Database

Semantic search and code retrieval:```bash

- Qdrant vector database integration# Test all service connections

- Azure OpenAI embeddings (text-embedding-3-large, 3072-dim)python test_connections.py

- Efficient batch processing

- Health monitoring# Test specific service

python test_connections.py confluence

### 3. LLM Orchestrationpython test_connections.py jira

Intelligent LLM provider management:python test_connections.py github

- Primary: Azure OpenAI (gpt-4.1-mini)python test_connections.py azure

- Fallback: Together AIpython test_connections.py together

- Auto-detection based on configurationpython test_connections.py vector

- Role-based provider selection```



### 4. Voice Assistant## 📖 Documentation Guidelines

Multilingual voice interactions:

- Azure Speech Services (STT/TTS)When adding new documentation:

- Language detection

- Translation support1. **Place in appropriate category folder**

- Meeting transcription2. **Use clear, descriptive filenames**

3. **Add entry to this README**

## 🔧 Configuration4. **Include proper markdown formatting**

5. **Add relevant tags and categories**

### Required Environment Variables

## 🤝 Contributing

```bash

# Primary LLM Provider (Azure OpenAI - Recommended)- Documentation follows markdown standards

AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/- Include code examples where applicable

AZURE_OPENAI_API_KEY=your-key- Keep documentation up-to-date with code changes

AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini- Use consistent formatting and structure



# Embeddings---

EMBEDDING_PROVIDER=azure

AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large**Need help?** Check the [Quick Start Guide](./setup/QUICK_START.md) or [Configuration Guide](./setup/CONFIGURATION_GUIDE.md).
AZURE_OPENAI_EMBEDDING_API_VERSION=2023-05-15

# Vector Database
QDRANT_URL=http://localhost:6333

# Optional: Fallback Provider
TOGETHER_API_KEY=your-together-api-key
```

See [Configuration Guide](setup/CONFIGURATION_GUIDE.md) for complete setup.

## 🧪 Testing

### Test All Services
```bash
python test_connections.py
```

### Test Specific Services
```bash
python test_azure_config.py              # Azure OpenAI
python test_embeddings.py                # Embeddings
python test_chat_completion_config.py    # Chat completion
python test_llm_provider_auto_detection.py  # Provider detection
```

### Run Code Intelligence Tests
```bash
cd code-intelligence
python orchestrator.py test
```

## 📁 Project Structure

```
ai-bots/
├── code-intelligence/       # Repository embedding and analysis
│   ├── orchestrator.py     # Main entry point
│   ├── embed_repo.py       # Embedding pipeline
│   ├── enhanced_summarizer.py  # Code summarization
│   └── README.md           # Module documentation
├── docs/                   # Documentation
│   ├── setup/              # Setup guides
│   ├── testing/            # Testing guides
│   ├── deployment/         # Deployment guides
│   └── archive/            # Historical documentation
├── interfaces/             # API endpoints
│   ├── http_api.py         # Main API
│   ├── vector_db_api.py    # Vector DB endpoints
│   └── code_intelligence_api.py  # Code intelligence endpoints
├── shared/                 # Shared modules
│   ├── vector_db/          # Vector database services
│   ├── llm_providers/      # LLM provider implementations
│   └── config.py           # Configuration management
├── orchestration/          # Orchestration layer
├── .env                    # Environment configuration
└── main.py                 # Application entry point
```

## 🔗 Quick Links

- **Main README**: [`../README.md`](../README.md)
- **Code Intelligence**: [`../code-intelligence/README.md`](../code-intelligence/README.md)
- **Configuration**: [`.env.example`](../.env.example)
- **API Documentation**: [`api/README.md`](api/README.md)

## 📚 Additional Resources

### Archived Documentation
Historical documentation and migration guides are available in [`archive/`](archive/):
- Azure integration history
- Migration plans
- Implementation status reports
- Executive summaries

### External Links
- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Together AI Documentation](https://docs.together.ai/)

## 🆘 Troubleshooting

### Common Issues

**1. "Embedding service not connected"**
```bash
# Check configuration
python orchestrator.py health

# Verify .env settings
# Ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set
```

**2. "429 Too Many Requests"**
```bash
# Adjust rate limiting in .env
AZURE_OPENAI_EMBEDDING_BATCH_SIZE=10  # Reduce from 20
AZURE_OPENAI_EMBEDDING_BATCH_DELAY=2.0  # Increase from 1.0
```

**3. "Qdrant connection failed"**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Or verify local storage path
ls ./qdrant_data
```

**4. "Module not found" errors**
```bash
# Ensure you're in the correct directory
cd a:\InfraCode\AM-Portfolio\ai-bots

# Install dependencies
pip install -r requirements.txt
```

For more help, see:
- [Testing Guide](testing/README.md)
- [Configuration Guide](setup/CONFIGURATION_GUIDE.md)
- [Architecture Documentation](ARCHITECTURE.md)

## 🤝 Contributing

When adding documentation:
1. Keep it feature-focused
2. Include code examples
3. Update this index
4. Archive outdated content

## 📝 Documentation Status

**Active Documentation:**
- ✅ Setup & Configuration
- ✅ Code Intelligence
- ✅ Testing Guides
- ✅ Architecture Diagrams
- ✅ API Documentation

**Archived:**
- Historical migration guides
- Implementation status reports
- Azure integration planning docs

Last Updated: October 22, 2025
