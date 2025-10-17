# UI Testing Guide - AI Development Agent

## Overview

The AI Development Agent now includes a **comprehensive Streamlit-based testing UI** that allows you to test all features individually and run complete workflows through an intuitive interface.

---

## 🚀 Quick Start

### Accessing the UI

The testing UI is running on port 8501:

**In Replit:**
- The UI is accessible via the Streamlit workflow
- Look for the "UI" tab in the workflow panel
- Or access via: `https://your-replit-url:8501`

**Locally:**
- Access at: `http://localhost:8501`

### Starting the UI

Both workflows are configured to run automatically:
- **Server (Port 5000)**: FastAPI backend
- **UI (Port 8501)**: Streamlit testing interface

To restart manually:
```bash
# Server
python main.py

# UI (in separate terminal)
cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🎯 Testing Interface Features

The UI is organized into **9 tabs**, each testing a specific component or workflow:

### 1. 🧠 LLM Testing

Test LLM providers (Together AI or Azure OpenAI) with custom prompts.

**What it tests:**
- LLM provider connectivity
- Chat completion functionality
- Provider switching (Together AI / Azure)

**How to use:**
1. Enter your prompt in the text area
2. Select provider (Together AI is default)
3. Click "Test LLM"
4. View the AI response

**Example use:**
- Prompt: "Explain async/await in Python"
- Provider: Together AI
- Expected: Detailed explanation from Llama-3.3-70B model

---

### 2. 🐙 GitHub Integration

Test GitHub API integration and issue retrieval.

**What it tests:**
- GitHub client connectivity
- Issue fetching with filters
- API token validation

**How to use:**
1. Enter repository in format: `owner/repo`
2. Click "Test GitHub"
3. View open bug issues from the repository

**Example use:**
- Repository: `microsoft/vscode`
- Expected: List of open bugs

---

### 3. 📋 Jira Integration

Test Jira API integration and ticket retrieval.

**What it tests:**
- Jira client connectivity
- JQL query execution
- Issue fetching

**How to use:**
1. Enter Jira project key (e.g., "PROJ")
2. Click "Test Jira"
3. View open issues from the project

**Example use:**
- Project Key: `DEMO`
- Expected: List of open issues

---

### 4. 📚 Confluence Integration

Test Confluence API integration and page retrieval.

**What it tests:**
- Confluence client connectivity
- Page search functionality
- Space access

**How to use:**
1. Enter Confluence space key
2. Click "Test Confluence"
3. View pages from the space

**Example use:**
- Space Key: `DEV`
- Expected: List of pages in DEV space

---

### 5. 📊 Grafana Integration

Test Grafana API integration and alert retrieval.

**What it tests:**
- Grafana client connectivity
- Alert fetching
- API key validation

**How to use:**
1. Click "Test Grafana"
2. View alerts from Grafana

**Example use:**
- Expected: List of Grafana alerts

---

### 6. 🔄 Context Resolver

Test the context enrichment system.

**What it tests:**
- Context resolver feature
- Multi-source data aggregation
- Related issues, code, logs, metrics extraction

**How to use:**
1. Enter issue ID
2. Select source (GitHub/Jira/Grafana)
3. Enter repository if using GitHub
4. Click "Test Context Resolver"
5. View enriched context data

**Example use:**
- Issue ID: `123`
- Source: GitHub
- Repository: `owner/repo`
- Expected: Enriched context with code, logs, metrics

---

### 7. 🔍 Code Analysis

Test LLM-powered code analysis.

**What it tests:**
- Code analysis feature
- Root cause identification
- Fix suggestions

**How to use:**
1. Enter code to analyze
2. Enter context (e.g., "login system")
3. Click "Analyze Code"
4. View analysis results with root cause, fixes, explanations

**Example use:**
- Code: Buggy authentication function
- Context: "User authentication system"
- Expected: Root cause analysis and suggested fixes

---

### 8. ✅ Test Generation

Test automated test generation.

**What it tests:**
- Test generation feature
- LLM test code creation
- Multi-language support

**How to use:**
1. Enter code to generate tests for
2. Select language (Python/JavaScript/Java)
3. Click "Generate Tests"
4. View generated test code

**Example use:**
- Code: Simple utility functions
- Language: Python
- Expected: Complete unit tests with pytest

---

### 9. 🚀 Full Analysis Workflow

Test the complete end-to-end workflow.

**What it tests:**
- Complete analysis pipeline
- Context resolution → Analysis → Fix generation → PR creation → Documentation

**How to use:**
1. Enter issue ID
2. Select source (GitHub/Jira/Grafana)
3. Enter repository
4. Enable options:
   - ✓ Create Pull Request
   - ✓ Publish Documentation (requires Confluence space)
5. Click "Run Full Analysis"
6. View complete results

**Example use:**
- Issue ID: `456`
- Source: GitHub
- Repository: `owner/repo`
- Create PR: ✓
- Publish Docs: ✓
- Confluence Space: `DEV`
- Expected: Analysis + Fixes + PR URL + Doc page

---

## 📡 Test API Endpoints

The following REST endpoints are available for testing:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/test/llm` | POST | Test LLM provider |
| `/api/test/github` | POST | Test GitHub integration |
| `/api/test/jira` | POST | Test Jira integration |
| `/api/test/confluence` | POST | Test Confluence integration |
| `/api/test/grafana` | POST | Test Grafana integration |
| `/api/test/context-resolver` | POST | Test context resolver |
| `/api/test/code-analysis` | POST | Test code analysis |
| `/api/test/generate-tests` | POST | Test test generation |

### Testing with cURL

```bash
# Test LLM
curl -X POST "http://localhost:5000/api/test/llm?prompt=Hello&provider=together"

# Test GitHub
curl -X POST "http://localhost:5000/api/test/github?repository=owner/repo"

# Test code analysis
curl -X POST "http://localhost:5000/api/test/code-analysis?code=def+foo():&context=test"
```

---

## 🔧 Configuration for Testing

### Required Environment Variables

For full functionality, configure these in `.env`:

```env
# LLM Provider (choose one or both)
LLM_PROVIDER=together
TOGETHER_API_KEY=your-together-api-key

# Or use Azure OpenAI
# LLM_PROVIDER=azure
# AZURE_OPENAI_ENDPOINT=https://...
# AZURE_OPENAI_API_KEY=your-key

# GitHub (for GitHub tests)
GITHUB_TOKEN=your-github-token

# Jira (for Jira tests)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-token

# Confluence (for Confluence/docs tests)
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-token

# Grafana (for Grafana tests)
GRAFANA_URL=https://your-grafana.com
GRAFANA_API_KEY=your-api-key
```

### Testing Without Configuration

The UI works even without full configuration:

- **✅ UI loads and shows API health status**
- **✅ Can test individual features (will show configuration errors)**
- **✅ Can see error messages guiding what to configure**

---

## 📊 Health Check

The UI shows API health status at the top:

- ✅ **Green**: API is healthy and running
- ❌ **Red**: API is not responding

If the API is unhealthy, check:
1. Server workflow is running
2. Port 5000 is accessible
3. No firewall blocking connections

---

## 🎨 UI Architecture

### Directory Structure

```
ui/
├── __init__.py          # Package marker
├── api_client.py        # API integration layer
└── app.py              # Main Streamlit application
```

### API Client (`api_client.py`)

Handles all backend communication:
- Automatic URL detection (Replit or localhost)
- Request/response handling
- Error management
- Timeout configuration

### Main App (`app.py`)

Streamlit UI with:
- 9 tabbed interfaces for testing
- Real-time API health monitoring
- Comprehensive error handling
- JSON response display
- Code syntax highlighting

---

## 🧪 Testing Workflows

### Individual Feature Testing

Test each component in isolation:

1. **LLM Provider**
   - Tab: LLM Testing
   - Verify: Together AI or Azure OpenAI responds

2. **External Integrations**
   - Tabs: GitHub, Jira, Confluence, Grafana
   - Verify: Data retrieval from each service

3. **Core Features**
   - Tabs: Context Resolver, Code Analysis, Test Generation
   - Verify: Features work with LLM provider

### Integrated Testing

Test complete workflows:

1. **Full Analysis Pipeline**
   - Tab: Full Analysis Workflow
   - Test: Complete issue → analysis → fix → PR → docs flow
   - Verify: All steps execute successfully

2. **Multi-Service Integration**
   - Use GitHub issues with context resolver
   - Generate fixes and create PRs
   - Publish documentation to Confluence

---

## 🐛 Troubleshooting

### UI Not Loading

**Issue**: Streamlit UI not accessible

**Solutions**:
1. Check UI workflow status
2. Verify port 8501 is not blocked
3. Restart UI workflow:
   ```bash
   cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
   ```

### API Connection Errors

**Issue**: "API is not responding"

**Solutions**:
1. Check Server workflow is running
2. Verify API is on port 5000
3. Check firewall rules
4. Test manually: `curl http://localhost:5000/health`

### LLM Provider Errors

**Issue**: "LLM provider not available"

**Solutions**:
1. Configure API key in `.env`:
   ```env
   TOGETHER_API_KEY=your-key
   ```
2. Restart Server workflow
3. Test in LLM Testing tab

### Integration Errors

**Issue**: GitHub/Jira/Confluence errors

**Solutions**:
1. Verify credentials in `.env`
2. Check API tokens are valid
3. Test connectivity outside the app
4. Review error messages for specific issues

---

## 📈 Advanced Usage

### Custom API Base URL

Override the API URL in the client:

```python
# In ui/api_client.py
api_client = APIClient(base_url="http://custom-host:5000")
```

### Adding New Test Endpoints

1. **Add API endpoint** in `interfaces/http_api.py`:
   ```python
   @app.post("/api/test/new-feature")
   async def test_new_feature(param: str):
       # Implementation
       return {"success": True}
   ```

2. **Add client method** in `ui/api_client.py`:
   ```python
   def test_new_feature(self, param: str):
       response = requests.post(
           f"{self.base_url}/api/test/new-feature",
           params={"param": param}
       )
       return response.json()
   ```

3. **Add UI tab** in `ui/app.py`:
   ```python
   with tabs[9]:
       st.header("New Feature Testing")
       param = st.text_input("Parameter")
       if st.button("Test"):
           result = api_client.test_new_feature(param)
           st.json(result)
   ```

---

## 📝 Best Practices

### Testing Checklist

Before deploying or using in production:

- [ ] Test LLM provider connectivity
- [ ] Verify external integrations (GitHub, Jira, etc.)
- [ ] Test context resolver with real issues
- [ ] Validate code analysis accuracy
- [ ] Confirm test generation quality
- [ ] Run complete workflow end-to-end
- [ ] Check PR creation (if enabled)
- [ ] Verify documentation publishing (if enabled)

### Security Considerations

1. **API Keys**: Never commit `.env` file
2. **Access Control**: UI has no authentication (add if needed)
3. **CORS**: Configured for testing (tighten for production)
4. **SSL**: Use HTTPS in production environments

---

## 🎯 Summary

The testing UI provides:

✅ **Comprehensive testing** of all features  
✅ **Individual component validation**  
✅ **Complete workflow testing**  
✅ **Real-time error feedback**  
✅ **Easy configuration validation**  
✅ **No code required** - all through UI  

Access the UI at **port 8501** and start testing all features of the AI Development Agent!

---

## 📞 Quick Reference

**UI URL**: `http://localhost:8501` (or Replit URL with :8501)  
**API URL**: `http://localhost:5000`  
**Main App**: `ui/app.py`  
**API Client**: `ui/api_client.py`  
**Test Endpoints**: `/api/test/*`  

**Restart Commands**:
```bash
# Server
python main.py

# UI
cd ui && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Happy Testing! 🚀
