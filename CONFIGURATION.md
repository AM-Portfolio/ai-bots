# Configuration Guide

Complete setup instructions for all integrations and services.

## Table of Contents
- [Environment Variables](#environment-variables)
- [Azure Configuration](#azure-configuration)
- [GitHub Setup](#github-setup)
- [Jira Setup](#jira-setup)
- [Confluence Setup](#confluence-setup)
- [Grafana Setup](#grafana-setup)
- [Microsoft Teams Bot](#microsoft-teams-bot)
- [Database Configuration](#database-configuration)
- [Webhook Configuration](#webhook-configuration)

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# ===== Azure Configuration =====
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# ===== Azure OpenAI =====
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# ===== GitHub =====
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_ORG=your-organization

# ===== Jira =====
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-token

# ===== Confluence =====
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-confluence-token

# ===== Grafana =====
GRAFANA_URL=https://your-grafana.com
GRAFANA_API_KEY=your-grafana-key

# ===== Database =====
DATABASE_URL=sqlite:///./ai_dev_agent.db
# For PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/ai_dev_agent

# ===== Microsoft Teams Bot =====
MICROSOFT_APP_ID=your-app-id
MICROSOFT_APP_PASSWORD=your-app-password

# ===== Application Settings =====
APP_HOST=0.0.0.0
APP_PORT=5000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## Azure Configuration

### 1. Azure Key Vault (Optional)

If using Azure Key Vault for secret management:

**Create Key Vault:**
```bash
az keyvault create \
  --name your-keyvault-name \
  --resource-group your-resource-group \
  --location eastus
```

**Create Service Principal:**
```bash
az ad sp create-for-rbac \
  --name ai-dev-agent \
  --role "Key Vault Secrets User" \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.KeyVault/vaults/{vault-name}
```

This returns:
```json
{
  "appId": "your-client-id",
  "password": "your-client-secret",
  "tenant": "your-tenant-id"
}
```

**Set Environment Variables:**
```env
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
```

### 2. Azure OpenAI

**Create Azure OpenAI Resource:**
1. Go to Azure Portal
2. Create "Azure OpenAI" resource
3. Deploy a model (e.g., gpt-4)

**Get Credentials:**
1. Navigate to your Azure OpenAI resource
2. Go to "Keys and Endpoint"
3. Copy:
   - Endpoint URL
   - API Key

**Configure:**
```env
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=abc123...
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## GitHub Setup

### 1. Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
4. Generate and copy the token

**Configure:**
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_ORG=your-organization-name
```

### 2. Configure Webhooks

**For each repository:**

1. Go to Repository Settings → Webhooks → Add webhook
2. Set Payload URL: `https://your-app-url.com/api/webhook/github`
3. Content type: `application/json`
4. Select events:
   - Issues
   - Pull requests
   - Push
5. Add webhook

**Webhook Payload Example:**
```json
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Bug in user service",
    "labels": [{"name": "bug"}]
  },
  "repository": {
    "full_name": "owner/repo"
  }
}
```

---

## Jira Setup

### 1. Create API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it (e.g., "AI Dev Agent")
4. Copy the token immediately (it won't be shown again)

**Configure:**
```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=ATATTxxxxxxxxxxxxxx
```

### 2. Test Connection

```python
from shared.clients import JiraClient

client = JiraClient()
issue = client.get_issue("PROJ-123")
print(issue)
```

### 3. Configure Webhooks (Optional)

1. Go to Jira Settings → System → WebHooks
2. Create webhook with URL: `https://your-app-url.com/api/webhook/jira`
3. Select events: Issue created, Issue updated

---

## Confluence Setup

### 1. Create API Token

Same process as Jira (they share the same token system):

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create token or use existing one
3. Copy token

**Configure:**
```env
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=ATATTxxxxxxxxxxxxxx
```

### 2. Get Space Key

1. Go to your Confluence space
2. Space key is visible in the URL: `https://domain.atlassian.net/wiki/spaces/DEV`
3. In this example, space key is `DEV`

### 3. Test Connection

```python
from shared.clients import ConfluenceClient

client = ConfluenceClient()
page = client.create_page(
    space_key="DEV",
    title="Test Page",
    content="<p>Test content</p>"
)
print(page)
```

---

## Grafana Setup

### 1. Create Service Account

1. Go to Grafana → Configuration → Service Accounts
2. Create new service account: "AI Dev Agent"
3. Add role: "Viewer" or "Editor"
4. Generate service account token
5. Copy token

**Configure:**
```env
GRAFANA_URL=https://your-grafana.com
GRAFANA_API_KEY=glsa_xxxxxxxxxxxxx
```

### 2. Configure Alert Webhooks

1. Go to Alerting → Contact points
2. Add contact point
3. Type: Webhook
4. URL: `https://your-app-url.com/api/webhook/grafana`

**Alert Payload Example:**
```json
{
  "event_type": "alert",
  "data": {
    "state": "alerting",
    "title": "High error rate",
    "message": "Error rate above threshold"
  }
}
```

---

## Microsoft Teams Bot

### 1. Register Bot in Azure

1. Go to Azure Portal → Create "Azure Bot"
2. Create new Microsoft App ID:
   - Type: Multi-tenant
   - Note the App ID and generate a client secret

**Configure:**
```env
MICROSOFT_APP_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_APP_PASSWORD=your-client-secret
```

### 2. Set Messaging Endpoint

In Azure Bot configuration:
```
https://your-app-url.com/api/teams/messages
```

### 3. Add to Teams

1. In Azure Bot, go to "Channels"
2. Add "Microsoft Teams" channel
3. Open in Teams and start conversation

### 4. Bot Commands

Users can interact with:
```
analyze github 123
status
help
```

---

## Database Configuration

### SQLite (Default)

No configuration needed. Database file created automatically:
```env
DATABASE_URL=sqlite:///./ai_dev_agent.db
```

### PostgreSQL (Production)

**Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# macOS
brew install postgresql
```

**Create Database:**
```sql
CREATE DATABASE ai_dev_agent;
CREATE USER aiagent WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_dev_agent TO aiagent;
```

**Configure:**
```env
DATABASE_URL=postgresql://aiagent:secure_password@localhost:5432/ai_dev_agent
```

**Run Migrations:**
```bash
alembic upgrade head
```

---

## Webhook Configuration

### Webhook Endpoints

| Service | Endpoint | Method | Content-Type |
|---------|----------|--------|--------------|
| GitHub | `/api/webhook/github` | POST | application/json |
| Grafana | `/api/webhook/grafana` | POST | application/json |
| Jira | `/api/webhook/jira` | POST | application/json |

### Security Best Practices

1. **Use HTTPS**: Always use secure connections
2. **Validate Signatures**: Implement webhook signature validation
3. **IP Whitelisting**: Restrict to known service IPs
4. **Rate Limiting**: Implement rate limits on webhook endpoints

### Testing Webhooks Locally

Use ngrok for local testing:
```bash
ngrok http 5000
```

Then use the ngrok URL for webhook configuration:
```
https://abc123.ngrok.io/api/webhook/github
```

---

## API Endpoint Reference

### Base URL
```
http://0.0.0.0:5000
```

### Authentication
Currently no authentication required. For production, implement:
- API keys
- OAuth 2.0
- JWT tokens

### Endpoints

**1. Health Check**
```bash
curl http://localhost:5000/health
```

**2. Analyze Issue**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "123",
    "source": "github",
    "repository": "owner/repo",
    "create_pr": true
  }'
```

**3. Metrics**
```bash
curl http://localhost:5000/metrics
```

---

## Troubleshooting

### Common Issues

**1. "Azure OpenAI credentials not configured"**
- Ensure `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY` are set in `.env`
- Verify the endpoint URL is correct
- Check API key has not expired

**2. "GitHub token not configured"**
- Create a personal access token
- Ensure `repo` scope is selected
- Set `GITHUB_TOKEN` in `.env`

**3. Database connection errors**
- For SQLite: ensure write permissions in project directory
- For PostgreSQL: verify connection string and database exists
- Check firewall rules

**4. Webhook not receiving events**
- Verify webhook URL is accessible from the internet
- Check webhook secret/signature validation
- Review webhook delivery logs in the service (GitHub/Grafana/Jira)

### Logs

Check application logs:
```bash
tail -f logs/app.log
```

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

---

## Production Deployment

### Environment Variables
- Store secrets in environment variables, not in code
- Use Azure Key Vault for production secrets
- Never commit `.env` file

### Database
- Use PostgreSQL or other production database
- Enable connection pooling
- Set up regular backups

### Monitoring
- Enable Prometheus metrics export
- Set up alerting on critical metrics
- Monitor API response times

### Security
- Implement authentication/authorization
- Use HTTPS only
- Enable rate limiting
- Validate all webhook signatures
- Keep dependencies updated

---

## Support

For additional help:
- Check application logs
- Review error messages
- Consult service documentation (GitHub, Jira, Azure, etc.)
- Contact development team
