# API Documentation

Complete API reference and endpoints for the AI Bots platform.

## 📋 Available Documentation

### [API_ENDPOINTS.md](./API_ENDPOINTS.md)
Complete API reference including:
- **Health Check Endpoints** - System health and status
- **Issue Analysis** - Analyze issues from various sources
- **Code Generation** - Generate fixes and tests
- **Documentation Publishing** - Confluence integration
- **Pull Request Creation** - GitHub integration
- **Webhook Handlers** - Event-driven processing

## 🚀 Quick API Reference

### Base URL
```
Production: https://your-app.repl.co
Local: http://localhost:5000
```

### Authentication
Most endpoints require proper authentication headers. See the main API documentation for details.

### Common Endpoints

```bash
# Health check
GET /health

# Analyze an issue
POST /api/analyze
{
  "issue_id": "123",
  "source": "github",
  "repository": "owner/repo"
}

# Get analysis status
GET /api/analyze/{analysis_id}/status
```

## 📚 Related Documentation
- [Configuration Guide](../setup/CONFIGURATION_GUIDE.md) - API configuration
- [Testing Guide](../testing/) - API testing procedures
- [Deployment Guide](../deployment/) - API deployment