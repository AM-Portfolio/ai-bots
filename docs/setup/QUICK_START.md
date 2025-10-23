# Quick Start Guide

Get the AI Development Agent running in 5 minutes!

## 1. Running the Application

The application is already configured and running at:
```
http://0.0.0.0:5000
```

To restart manually:
```bash
python main.py
```

## 2. Test the API

### Check if it's running:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{"status": "healthy"}
```

### Get service info:
```bash
curl http://localhost:5000/
```

## 3. Basic Configuration (Optional)

Create a `.env` file from the example:
```bash
cp .env.example .env
```

### Minimal Setup (AI Features Only)

Add to `.env`:
```env
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
```

### GitHub Integration

Add to `.env`:
```env
GITHUB_TOKEN=ghp_your_token_here
```

## 4. Try the Analysis API

### Without External Services (Demo Mode):
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "issue_id": "demo",
    "source": "github",
    "repository": "test/repo",
    "create_pr": false
  }'
```

### With GitHub (After Configuration):
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

## 5. Set Up Webhooks

### GitHub Webhook
1. Go to your repo → Settings → Webhooks
2. Add webhook URL: `https://your-app.com/api/webhook/github`
3. Select events: Issues, Pull requests
4. Save

### Grafana Alert
1. Go to Alerting → Contact points
2. Add webhook: `https://your-app.com/api/webhook/grafana`
3. Save

## 6. View Metrics

```bash
curl http://localhost:5000/metrics
```

## 7. Microsoft Teams Bot (Optional)

In Teams, chat with your bot:
```
analyze github 123
status
help
```

## 8. Check Logs

```bash
# View recent logs
tail -f logs/*.log
```

## Next Steps

- **Full Configuration**: See [CONFIGURATION.md](CONFIGURATION.md)
- **API Documentation**: See [API_ENDPOINTS.md](API_ENDPOINTS.md)
- **Architecture**: See [README.md](README.md)

## Troubleshooting

**"Azure OpenAI credentials not configured"**
- Add credentials to `.env` file
- Restart the server

**"GitHub token not configured"**
- Create token at GitHub Settings → Developer settings
- Add to `.env` as `GITHUB_TOKEN`

**Port already in use**
- Change `APP_PORT` in `.env`
- Or stop other process using port 5000

## Support

Check the documentation or review application logs for detailed error messages.
