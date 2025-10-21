# Service Connection Tests

This directory contains comprehensive test suites for all service connections used by the AI Bots project.

## Quick Start

To test all service connections at once:

```bash
python test_connections.py
```

To test a specific service:

```bash
python test_connections.py <service_name>
```

Available services: `azure`, `together`, `github`, `confluence`, `jira`, `vector`

## Test Files

### Individual Service Tests

- **`test_azure.py`** - Tests Azure services (Key Vault, OpenAI)
- **`test_together.py`** - Tests Together AI API and available models  
- **`test_github.py`** - Tests GitHub API, organization and repository access
- **`test_confluence.py`** - Tests Confluence API, spaces, and page creation
- **`test_jira.py`** - Tests Jira API, projects, and issue creation
- **`test_vector.py`** - Tests vector database (Qdrant) and embedding services

### Master Test Runner

- **`test_all.py`** - Master test runner that coordinates all service tests
- **`../test_connections.py`** - Main entry point script (run from project root)

## What Each Test Checks

### Configuration
- Verifies that all required environment variables are set
- Checks if API keys and credentials are properly configured

### Connection
- Tests actual network connectivity to each service
- Validates authentication credentials
- Measures response times and success rates

### Operations
- Tests basic CRUD operations where applicable
- Verifies permissions and access levels
- Tests service-specific functionality

## Output Format

Each test provides:

1. **Configuration Status** - Whether the service is properly configured
2. **Connection Status** - Whether the service is reachable and authenticated
3. **Error Details** - Specific error messages for failed connections
4. **Service Details** - Additional information about the service state
5. **Summary Statistics** - Overall success rates and counts

## Example Output

```
CONNECTION TEST RESULTS - 2025-10-21T13:35:17.057233
============================================================

OVERALL SUMMARY:
  Service categories tested: 6
  Healthy categories: 5
  Total services: 24
  Configured services: 20
  Connected services: 18
  Success rate: 18/20

----------------------------------------
CONFLUENCE SERVICES
----------------------------------------
  Configured: 4/4
  Connected: 3/4
  Success rate: 3/4

  Confluence API:
    Configured: True
    Connected: True
    Details: {'url': 'https://...', 'space_key': '...'}
```

## Configuration Requirements

Make sure your `.env` file contains all necessary credentials:

```env
# Azure
AZURE_TENANT_ID=your-tenant-id
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# Together AI
TOGETHER_API_KEY=your-together-api-key

# GitHub
GITHUB_TOKEN=your-github-token
GITHUB_ORG=your-organization

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@domain.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=your-space-key

# Jira
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=your-project-key

# Vector DB (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   - Install required packages: `pip install -r requirements.txt`

2. **API Token Issues**
   - Verify tokens are not expired
   - Check token permissions and scopes

3. **Network Connectivity**
   - Verify firewall settings
   - Check if services are accessible from your network

4. **Configuration Errors**
   - Ensure `.env` file is in the project root
   - Verify environment variable names match exactly

### Debug Mode

For detailed debugging, you can run individual test files directly:

```bash
python -m shared.tests.test_confluence
```

This will provide more detailed output and stack traces for debugging.

## Extending Tests

To add a new service test:

1. Create a new test file in `shared/tests/test_<service>.py`
2. Follow the existing pattern with async test functions
3. Add the test function to `test_all.py` in the `test_functions` dictionary
4. Update this README with the new service information

Each test function should return a dictionary with the following structure:

```python
{
    "service": "Service Name",
    "configured": bool,  # Whether the service is configured
    "connection": bool,  # Whether the connection succeeded
    "error": str | None,  # Error message if any
    "details": dict      # Additional service-specific information
}
```