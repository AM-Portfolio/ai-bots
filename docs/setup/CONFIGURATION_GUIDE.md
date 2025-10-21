# AI Dev Agent - Configuration Guide

## ✅ Current Configuration Status

Your application is now configured and running with **ENV-based configuration** for:

### 🤖 Together AI (Primary LLM Provider)
- **Status**: ✅ Configured via ENV
- **API Key**: Set in `.env` as `TOGETHER_API_KEY`
- **Model**: `meta-llama/Llama-3.3-70B-Instruct-Turbo`
- **SDK Version**: 1.5.26 (upgraded from 0.2.11)
- **Provider Priority**: Default (primary)

### 🐙 GitHub Integration
- **Status**: ✅ Configured via ENV
- **Token**: Set in `.env` as `GITHUB_TOKEN`
- **Organization**: `AM-Portfolio`
- **Wrapper**: Using ENV config (not Replit connector)

### 📝 Confluence Integration
- **Status**: ✅ Configured via ENV
- **URL**: `https://modern-portfolio.atlassian.net/wiki`
- **Email**: `ssd2658@gmail.com`
- **API Token**: Set in `.env`

---

## 🔧 Environment Configuration

### Configuration Source Hierarchy

The application uses this priority order:
1. **ENV variables** (from `.env` file) - **HIGHEST PRIORITY**
2. **Replit connectors** (automatic fallback)
3. **Default values** (if neither available)

### ENV File Location

```
/workspace/.env
```

### Key Configuration Variables

```bash
# LLM Provider Configuration
LLM_PROVIDER=together
TOGETHER_API_KEY=bff39f38...  # Your Together AI API key
TOGETHER_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo

# GitHub Configuration
GITHUB_TOKEN=github_pat_...  # Your GitHub PAT
GITHUB_ORG=AM-Portfolio

# Confluence Configuration
CONFLUENCE_URL=https://modern-portfolio.atlassian.net/wiki
CONFLUENCE_EMAIL=ssd2658@gmail.com
CONFLUENCE_API_TOKEN=ATATT3xFfGF0...  # Your Confluence API token

# Jira Configuration (optional)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-token

# Azure OpenAI (fallback provider)
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Database
DATABASE_URL=sqlite:///./ai_dev_agent.db

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## 🎯 How Integration Wrappers Work

### Priority System

All integration wrappers follow this pattern:

1. **Try ENV config first**
   - Checks for ENV variables (e.g., `GITHUB_TOKEN`, `TOGETHER_API_KEY`)
   - If found, creates client using ENV config
   - Logs: `"✅ GitHub wrapper using ENV config (GITHUB_TOKEN)"`

2. **Fall back to Replit connector**
   - If ENV vars missing, tries Replit connector
   - Logs: `"🔄 GitHub wrapper using Replit connector (fallback)"`

3. **Report if neither available**
   - Returns `None` if both fail
   - Business logic handles gracefully

### Example: GitHub Wrapper

```python
# In shared/clients/wrappers/github_wrapper.py

def _initialize(self):
    """Initialize clients based on available configuration"""
    
    # Priority 1: ENV config
    if settings.github_token:
        try:
            from shared.clients.github_client import GitHubClient
            self._env_client = GitHubClient()
            self._active_provider = "env"
            logger.info("✅ GitHub wrapper using ENV config (GITHUB_TOKEN)")
        except Exception as e:
            logger.warning(f"Failed to initialize ENV-based GitHub client: {e}")
    
    # Priority 2: Replit connector (fallback)
    if not self._env_client:
        try:
            from shared.clients.github_replit_client import GitHubReplitClient
            self._replit_client = GitHubReplitClient()
            self._active_provider = "replit"
            logger.info("🔄 GitHub wrapper using Replit connector (fallback)")
        except Exception as e:
            logger.error(f"Failed to initialize Replit GitHub client: {e}")
```

### Benefits of This Approach

1. **Flexibility**: Easy to switch between ENV and Replit connectors
2. **Removability**: Can remove integrations without changing business logic
3. **Testing**: Can test with different configurations easily
4. **Portability**: Works in any environment (local, Replit, cloud)
5. **Clarity**: Logs show which provider is being used

---

## 🚀 How to Verify Configuration

### 1. Check ENV Loading

```bash
cd /home/runner/workspace
python -c "from shared.config import settings; print('GitHub Token:', 'SET' if settings.github_token else 'NOT SET'); print('Together API Key:', 'SET' if settings.together_api_key else 'NOT SET')"
```

**Expected Output:**
```
GitHub Token: SET
Together API Key: SET
```

### 2. Check Together AI SDK

```bash
python -c "from together import Together; client = Together(); print('Client has chat:', hasattr(client, 'chat'))"
```

**Expected Output:**
```
Client has chat: True
```

### 3. Check Application Logs

```bash
# Look for these log messages when the app starts:
✅ Together AI client initialized successfully
✅ GitHub wrapper using ENV config (GITHUB_TOKEN)
```

---

## 🔄 How to Change Configuration

### Switching Providers

To switch from Together AI to Azure OpenAI:

```bash
# In .env file
LLM_PROVIDER=azure  # Change from 'together' to 'azure'
```

The resilient orchestrator will automatically use Azure OpenAI as the primary provider.

### Switching GitHub Auth Method

**Option 1: Use ENV config (current)**
```bash
# Keep GITHUB_TOKEN in .env
GITHUB_TOKEN=github_pat_...
```

**Option 2: Use Replit connector**
```bash
# Remove or comment out GITHUB_TOKEN from .env
# GITHUB_TOKEN=github_pat_...

# The wrapper will automatically fall back to Replit connector
```

---

## 🛠️ Troubleshooting

### Together AI Issues

**Problem**: `'Together' object has no attribute 'chat'`

**Solution**: Upgrade Together SDK
```bash
pip install --upgrade together
```

**Verify**: Check SDK version
```bash
pip show together | grep Version
# Should show: Version: 1.5.26 or higher
```

### GitHub 401 Unauthorized

**Problem**: GitHub API returns 401 errors

**Possible Causes**:
1. Token expired
2. Token lacks required scopes
3. Token is invalid

**Solution**: Generate new GitHub PAT with these scopes:
- `repo` (full control of private repositories)
- `read:org` (read organization data)
- `workflow` (update GitHub Action workflows)

**Update `.env`**:
```bash
GITHUB_TOKEN=github_pat_NEW_TOKEN_HERE
```

### Configuration Not Loading

**Problem**: Changes to `.env` not taking effect

**Solution**: Restart the application
```bash
# The workflow auto-restarts when .env changes are detected
# Or manually restart via Replit UI
```

---

## 📊 Current System Status

### ✅ Working Features

1. **Together AI Integration**
   - SDK upgraded to 1.5.26
   - Chat completions API working
   - Streaming support enabled

2. **GitHub Integration**
   - Using ENV-based authentication
   - Wrapper pattern implemented
   - Easy fallback to Replit connector

3. **Confluence Integration**
   - ENV config loaded
   - API token configured
   - Ready for documentation publishing

4. **Frontend Logger**
   - Zustand-based reactive logging
   - 7 categories (Chat, Voice, API, LLM, Integrations, Orchestrator, UI)
   - Floating LogViewer with filtering

### 🎯 Integration Priority

All integrations now follow ENV-first pattern:

| Integration | ENV Config | Replit Connector | Active Provider |
|-------------|-----------|------------------|-----------------|
| Together AI | ✅ SET | N/A | ENV |
| GitHub | ✅ SET | Available | ENV |
| Confluence | ✅ SET | Available | ENV |
| Jira | ❌ NOT SET | Available | Not Active |
| Azure OpenAI | ❌ NOT SET | N/A | Fallback |

---

## 🔐 Security Best Practices

### Never Commit Secrets

The `.env` file is already in `.gitignore`. **Never commit**:
- API keys
- Tokens
- Passwords
- Client secrets

### Rotate Tokens Regularly

Schedule regular token rotation:
- GitHub PATs: Every 90 days
- API Keys: Every 90 days
- Service Account tokens: Every 30 days

### Use Minimum Required Scopes

GitHub PAT should only have:
- `repo` (if you need full control)
- `public_repo` (if you only need public repos)
- `read:org` (minimum for organization access)

---

## 📚 Additional Resources

### Environment Configuration
- **Config File**: `/workspace/shared/config.py`
- **ENV File**: `/workspace/.env`
- **Settings Class**: `shared.config.Settings`

### Integration Wrappers
- **GitHub**: `/workspace/shared/clients/wrappers/github_wrapper.py`
- **Jira**: `/workspace/shared/clients/wrappers/jira_wrapper.py`
- **Confluence**: `/workspace/shared/clients/wrappers/confluence_wrapper.py`

### LLM Providers
- **Together AI**: `/workspace/shared/llm_providers/together_provider.py`
- **Azure OpenAI**: `/workspace/shared/llm_providers/azure_provider.py`
- **Resilient Orchestrator**: `/workspace/shared/llm_providers/resilient_orchestrator.py`

### Frontend Logger
- **Logger Utility**: `/workspace/frontend/src/utils/logger.ts`
- **LogViewer Component**: `/workspace/frontend/src/components/Shared/LogViewer.tsx`
- **Logger Documentation**: `/workspace/frontend/src/utils/README_LOGGER.md`

---

## ✅ Verification Checklist

Before using the application, verify:

- [ ] Together AI API key is set in `.env`
- [ ] GitHub token is set in `.env`
- [ ] Confluence credentials are set (if using)
- [ ] Application logs show "Together AI client initialized successfully"
- [ ] Application logs show "GitHub wrapper using ENV config"
- [ ] Frontend loads without errors
- [ ] LogViewer shows log entries

---

## 🎉 You're All Set!

Your AI Dev Agent is now configured and running with:
- ✅ Together AI (primary LLM)
- ✅ GitHub integration (ENV config)
- ✅ Confluence integration (ENV config)
- ✅ Resilient LLM orchestration with automatic fallback
- ✅ Frontend activity logger with 7 categories
- ✅ Modular wrapper pattern for easy integration management

**Ready to use!** 🚀
