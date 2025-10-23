# User Guides

Comprehensive user guides and how-to documentation for the AI Bots platform.

## 📚 User Guides

### Core System Guides

#### [LLM_PROVIDER_GUIDE.md](./LLM_PROVIDER_GUIDE.md) 🤖
LLM provider configuration and usage:
- Provider comparison (Together AI vs Azure OpenAI)
- Configuration setup
- Best practices and optimization
- Troubleshooting common issues

#### [LOGGING_GUIDE.md](./LOGGING_GUIDE.md) 📊
Logging configuration and best practices:
- Log level configuration
- Structured logging setup
- Log analysis and monitoring
- Troubleshooting with logs

### Vector Database Guides

#### [VECTOR_DB_QUICKSTART.md](./VECTOR_DB_QUICKSTART.md) 🚀
**Quick start guide** for vector database setup:
- Qdrant installation and configuration
- Basic operations and testing
- Quick setup verification

#### [VECTOR_DB_USAGE.md](./VECTOR_DB_USAGE.md) 📖
Comprehensive vector database usage guide:
- Advanced Qdrant operations
- Vector search optimization
- Performance tuning
- Backup and maintenance

#### [QDRANT_REPOSITORY_INDEXING.md](./QDRANT_REPOSITORY_INDEXING.md) 🔍
Repository indexing with Qdrant:
- Code indexing strategies
- Search optimization
- Repository analysis workflows
- Semantic code search

## 🎯 Guide Categories

### 🤖 **AI & Machine Learning**
- LLM provider setup and optimization
- Model selection and configuration
- Performance tuning for AI operations

### 📊 **Data & Search**
- Vector database management
- Semantic search implementation
- Repository indexing strategies
- Search optimization techniques

### 🔧 **System Administration**
- Logging and monitoring setup
- Performance optimization
- Troubleshooting procedures
- Maintenance workflows

### 📈 **Analytics & Monitoring**
- Log analysis techniques
- Performance monitoring
- Usage analytics
- Health monitoring

## 🚀 Quick Start Workflow

1. **[LLM Setup](./LLM_PROVIDER_GUIDE.md)** - Configure AI providers
2. **[Vector DB Setup](./VECTOR_DB_QUICKSTART.md)** - Quick database setup
3. **[Logging Setup](./LOGGING_GUIDE.md)** - Configure monitoring
4. **[Repository Indexing](./QDRANT_REPOSITORY_INDEXING.md)** - Index your code

## 🔧 Common Tasks

### Setting up LLM Providers
```bash
# Test Together AI connection
python test_connections.py together

# Test Azure OpenAI connection  
python test_connections.py azure
```

### Vector Database Operations
```bash
# Test vector database connection
python test_connections.py vector

# Index a repository
python scripts/index_repository.py
```

### Monitoring and Logs
```bash
# Check application health
curl http://localhost:5000/health

# View logs in real-time
tail -f logs/app.log
```

## 📚 Related Documentation
- [Setup Guides](../setup/) - Initial configuration
- [Features](../features/) - Feature-specific guides
- [Testing](../testing/) - Testing procedures
- [API Documentation](../api/) - API reference