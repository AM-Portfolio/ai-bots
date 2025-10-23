# API Endpoints Documentation

Complete reference for all API endpoints.

## Base URL
```
http://0.0.0.0:5000
```

## Endpoints

### 1. Root / Health Check

**GET /**
```bash
curl http://localhost:5000/
```

**Response:**
```json
{
  "service": "AI Dev Agent",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "analyze": "/api/analyze",
    "webhook": "/api/webhook"
  }
}
```

---

### 2. Health Check

**GET /health**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 3. Analyze Issue

Analyzes an issue from GitHub, Jira, or other sources.

**POST /api/analyze**

**Request Body:**
```json
{
  "issue_id": "string",
  "source": "github|jira|grafana|confluence|teams",
  "repository": "string (required for GitHub)",
  "create_pr": boolean,
  "publish_docs": boolean,
  "confluence_space": "string (optional)"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "123",
    "source": "github",
    "repository": "owner/repo",
    "create_pr": true,
    "publish_docs": false
  }'
```

**Response:**
```json
{
  "issue_id": "123",
  "analysis": {
    "issue_id": "123",
    "root_cause": "NullPointerException in UserService.validateUser() due to missing null check",
    "affected_components": ["UserService", "AuthController"],
    "suggested_fixes": [
      {
        "file_path": "src/services/UserService.java",
        "original_code": "public boolean validateUser(User user) { return user.isValid(); }",
        "fixed_code": "public boolean validateUser(User user) { if (user == null) return false; return user.isValid(); }",
        "explanation": "Added null check before accessing user object",
        "test_code": "..."
      }
    ],
    "confidence_score": 0.95,
    "analysis_metadata": {}
  },
  "fixes_count": 1,
  "pr_url": "https://github.com/owner/repo/pull/456",
  "documentation_page": null
}
```

**Status Codes:**
- `200 OK` - Analysis successful
- `400 Bad Request` - Invalid request parameters
- `500 Internal Server Error` - Analysis failed

---

### 4. GitHub Webhook

Receives webhook events from GitHub.

**POST /api/webhook/github**

**GitHub Webhook Configuration:**
- **Payload URL:** `https://your-app.com/api/webhook/github`
- **Content type:** `application/json`
- **Events:** Issues, Pull requests

**Request Body (Issue Opened):**
```json
{
  "source": "github",
  "event_type": "issues",
  "data": {
    "action": "opened",
    "issue": {
      "number": 123,
      "title": "Bug in authentication",
      "body": "Users cannot log in...",
      "labels": [
        {"name": "bug"},
        {"name": "ai-fix"}
      ]
    },
    "repository": {
      "full_name": "owner/repo"
    }
  }
}
```

**Response:**
```json
{
  "status": "received"
}
```

**Automatic Processing:**
When an issue is labeled with `bug` or `ai-fix`, the system automatically:
1. Analyzes the issue
2. Generates fixes
3. Creates a pull request

---

### 5. Grafana Webhook

Receives alerts from Grafana.

**POST /api/webhook/grafana**

**Grafana Alert Configuration:**
- **Type:** Webhook
- **URL:** `https://your-app.com/api/webhook/grafana`

**Request Body:**
```json
{
  "source": "grafana",
  "event_type": "alert",
  "data": {
    "state": "alerting",
    "title": "High Error Rate",
    "message": "Error rate exceeded 5% threshold",
    "evalMatches": [
      {
        "metric": "error_rate",
        "value": 7.5
      }
    ]
  }
}
```

**Response:**
```json
{
  "status": "received"
}
```

---

### 6. Jira Webhook

Receives webhook events from Jira.

**POST /api/webhook/jira**

**Jira Webhook Configuration:**
- **URL:** `https://your-app.com/api/webhook/jira`
- **Events:** Issue created, Issue updated

**Request Body:**
```json
{
  "source": "jira",
  "event_type": "issue_created",
  "data": {
    "issue": {
      "key": "PROJ-123",
      "fields": {
        "summary": "Critical bug in payment processing",
        "issuetype": {"name": "Bug"},
        "priority": {"name": "Critical"}
      }
    }
  }
}
```

**Response:**
```json
{
  "status": "received"
}
```

---

### 7. Prometheus Metrics

Exposes metrics in Prometheus format.

**GET /metrics**

**cURL Example:**
```bash
curl http://localhost:5000/metrics
```

**Response (Prometheus format):**
```
# HELP ai_dev_agent_issues_analyzed_total Total number of issues analyzed
# TYPE ai_dev_agent_issues_analyzed_total counter
ai_dev_agent_issues_analyzed_total{severity="high",source="github"} 15.0
ai_dev_agent_issues_analyzed_total{severity="medium",source="jira"} 8.0

# HELP ai_dev_agent_fixes_generated_total Total number of fixes generated
# TYPE ai_dev_agent_fixes_generated_total counter
ai_dev_agent_fixes_generated_total 23.0

# HELP ai_dev_agent_prs_created_total Total number of PRs created
# TYPE ai_dev_agent_prs_created_total counter
ai_dev_agent_prs_created_total{repository="owner/repo"} 12.0

# HELP ai_dev_agent_analysis_duration_seconds Time spent analyzing issues
# TYPE ai_dev_agent_analysis_duration_seconds histogram
ai_dev_agent_analysis_duration_seconds_bucket{le="0.1"} 2.0
ai_dev_agent_analysis_duration_seconds_bucket{le="0.5"} 5.0
ai_dev_agent_analysis_duration_seconds_bucket{le="1.0"} 10.0
...
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request**
```json
{
  "detail": "Invalid request parameters"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error occurred"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement rate limiting per IP/API key
- Suggested: 100 requests per minute per client
- Return `429 Too Many Requests` when exceeded

---

## Authentication

Currently no authentication is required. For production, implement one of:

### 1. API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/analyze
```

### 2. Bearer Token
```bash
curl -H "Authorization: Bearer your-token" http://localhost:5000/api/analyze
```

### 3. OAuth 2.0
Standard OAuth 2.0 flow with client credentials or authorization code grant.

---

## WebSocket Support (Future)

For real-time updates, consider adding WebSocket endpoints:

**WS /ws/analysis/{issue_id}**

Stream analysis progress in real-time:
```json
{"status": "analyzing", "progress": 25}
{"status": "generating_fix", "progress": 50}
{"status": "creating_pr", "progress": 75}
{"status": "complete", "progress": 100, "pr_url": "..."}
```

---

## Pagination (Future)

For list endpoints, implement pagination:

```bash
GET /api/issues?page=1&limit=50
```

Response:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 50,
  "pages": 3
}
```

---

## Testing Endpoints

### Using cURL

**Test health:**
```bash
curl http://localhost:5000/health
```

**Test analysis:**
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "test-123",
    "source": "github",
    "repository": "test/repo"
  }'
```

### Using Python

```python
import requests

# Health check
response = requests.get("http://localhost:5000/health")
print(response.json())

# Analyze issue
data = {
    "issue_id": "123",
    "source": "github",
    "repository": "owner/repo",
    "create_pr": False
}
response = requests.post("http://localhost:5000/api/analyze", json=data)
print(response.json())
```

### Using Postman

1. Import the endpoints into Postman
2. Set base URL: `http://localhost:5000`
3. Create requests for each endpoint
4. Save as a collection for easy testing

---

## Integration Examples

### GitHub Actions Workflow

```yaml
name: AI Analysis
on:
  issues:
    types: [labeled]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - name: Analyze Issue
        run: |
          curl -X POST https://your-app.com/api/analyze \
            -H "Content-Type: application/json" \
            -d '{
              "issue_id": "${{ github.event.issue.number }}",
              "source": "github",
              "repository": "${{ github.repository }}",
              "create_pr": true
            }'
```

### Slack Integration

```python
# Slack bot that triggers analysis
@app.command("/analyze")
def analyze_command(ack, command):
    ack()
    
    requests.post("https://your-app.com/api/analyze", json={
        "issue_id": command["text"],
        "source": "jira",
        "create_pr": True
    })
```

---

## Support

For API support:
- Check logs for detailed error messages
- Review request/response in documentation
- Test with cURL before implementing in code
- Contact development team for assistance
