# Integration Wrappers

This directory contains unified wrapper classes for external service integrations. These wrappers provide a **single interface** that works with both traditional ENV-based authentication and Replit connectors.

## 🎯 Purpose

The wrapper pattern solves several key challenges:

1. **Flexibility**: Support both ENV config and Replit connectors
2. **Automatic Fallback**: Use ENV first, fall back to Replit if not configured
3. **Easy Migration**: Switch between providers without changing business logic
4. **Simple Removal**: Remove/replace integrations by updating one file
5. **Transparent**: Business logic doesn't know or care which provider is used

## 🏗️ Architecture

```
┌─────────────────────────┐
│   Business Logic        │
│   (Services, Features)  │
└───────────┬─────────────┘
            │
            │ Uses unified interface
            ▼
┌─────────────────────────┐
│   Wrapper Layer         │
│   (GitHubWrapper, etc)  │
└─────┬─────────────┬─────┘
      │             │
      │             │ Fallback
      ▼             ▼
┌──────────┐  ┌──────────────┐
│ ENV      │  │ Replit       │
│ Client   │  │ Connector    │
└──────────┘  └──────────────┘
```

## 📦 Available Wrappers

### GitHubWrapper

**ENV Config (Priority 1):**
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_ORG=your-org
```

**Replit Connector (Fallback):**
- Automatically uses Replit's GitHub integration
- No manual token management required

**Usage:**
```python
from shared.clients.wrappers import GitHubWrapper

wrapper = GitHubWrapper()

# Works with both ENV and Replit providers
issue = await wrapper.get_issue("owner/repo", 123)
pr = await wrapper.create_pull_request(
    repo_name="owner/repo",
    title="Fix bug",
    body="Description",
    head="feature-branch"
)
```

### JiraWrapper

**ENV Config (Priority 1):**
```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=ATATTxxxxxxxxxxxxxx
```

**Replit Connector (Fallback):**
- Not yet implemented
- Will use Replit's Jira integration when available

**Usage:**
```python
from shared.clients.wrappers import JiraWrapper

wrapper = JiraWrapper()

issue = await wrapper.get_issue("PROJ-123")
new_issue = await wrapper.create_issue(
    project_key="PROJ",
    summary="Bug found",
    description="Details here"
)
```

### ConfluenceWrapper

**ENV Config (Priority 1):**
```env
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=ATATTxxxxxxxxxxxxxx
```

**Replit Connector (Fallback):**
- Uses Replit's Confluence integration
- Automatic authentication

**Usage:**
```python
from shared.clients.wrappers import ConfluenceWrapper

wrapper = ConfluenceWrapper()

page = await wrapper.get_page("123456")
page_id = await wrapper.create_page(
    space_key="DEV",
    title="Documentation",
    content="<p>Content here</p>"
)
```

## 🔄 How It Works

### Initialization Flow

1. **Check ENV Config First**
   - Look for required environment variables
   - If found, initialize traditional client
   - Mark provider as "env"

2. **Fall Back to Replit Connector**
   - If ENV config missing or invalid
   - Try to initialize Replit connector
   - Mark provider as "replit"

3. **Log Provider Used**
   - Clear logging about which provider is active
   - Makes debugging easy

### Method Calls

```python
async def get_issue(self, repo_name: str, issue_number: int):
    if self._env_client:
        return self._env_client.get_issue(repo_name, issue_number)
    elif self._replit_client:
        return await self._replit_client.get_issue(repo_name, issue_number)
    else:
        logger.error("No provider configured")
        return None
```

Every method:
1. Tries ENV client first (synchronous)
2. Falls back to Replit client (async)
3. Logs error if neither available

## 🎨 Example Output

When ENV config is available:
```
✅ GitHub wrapper using ENV config (GITHUB_TOKEN)
```

When falling back to Replit:
```
🔄 GitHub wrapper using Replit connector (fallback)
```

When nothing is configured:
```
⚠️  GitHub wrapper: No ENV config or Replit connector available
```

## 🔧 Extending

To add a new integration wrapper:

1. **Create wrapper file** (e.g., `slack_wrapper.py`)
2. **Follow the pattern:**
   - Check ENV config first
   - Fall back to Replit connector
   - Provide unified interface
3. **Export from `__init__.py`**
4. **Document in this README**

Example skeleton:
```python
class SlackWrapper:
    def __init__(self):
        self._env_client = None
        self._replit_client = None
        self._active_provider = None
        self._initialize()
    
    def _initialize(self):
        if settings.slack_token:
            self._env_client = SlackClient()
            self._active_provider = "env"
        else:
            self._replit_client = SlackReplitClient()
            self._active_provider = "replit"
    
    async def send_message(self, channel: str, message: str):
        if self._env_client:
            return self._env_client.send_message(channel, message)
        elif self._replit_client:
            return await self._replit_client.send_message(channel, message)
```

## 🗑️ Removing Integrations

To remove an integration completely:

1. **Delete the wrapper file** (e.g., `github_wrapper.py`)
2. **Remove from `__init__.py`** exports
3. **Update business logic** to remove calls
4. **Remove ENV vars** from `.env`

The wrapper pattern makes removal clean and isolated!

## ✅ Benefits

1. **No Breaking Changes**: Business logic stays the same
2. **Progressive Migration**: Move from ENV to Replit gradually
3. **Easy Testing**: Mock the wrapper, not multiple clients
4. **Clear Logging**: Always know which provider is used
5. **Type Safety**: Unified interface with proper typing
6. **Error Handling**: Consistent error responses

## 🚀 Migration Guide

### Before (Direct Client Usage)
```python
from shared.clients.github_client import github_client

issue = github_client.get_issue("owner/repo", 123)
```

### After (Wrapper Usage)
```python
from shared.clients.wrappers import github_wrapper

issue = await github_wrapper.get_issue("owner/repo", 123)
```

That's it! The wrapper handles ENV vs Replit automatically.
