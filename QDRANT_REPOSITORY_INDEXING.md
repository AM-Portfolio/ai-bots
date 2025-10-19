# Qdrant Vector Database - Repository Indexing Guide

## Overview
This guide explains how to set up Qdrant vector database and re-index GitHub repositories for semantic code search and AI-powered analysis.

## Prerequisites
- Docker and Docker Compose installed
- GitHub access token configured (GITHUB_TOKEN environment variable)
- AI Dev Agent running

## Setup Qdrant

### 1. Start Qdrant with Docker Compose

```bash
# Start Qdrant container
docker-compose up -d

# Verify Qdrant is running
docker-compose ps
curl http://localhost:6333/health
```

Expected output:
```json
{"title":"qdrant - vector search engine","version":"1.x.x"}
```

### 2. Access Qdrant Dashboard

Open your browser to: `http://localhost:6333/dashboard`

The dashboard provides:
- Collection management
- Point inspection
- Search testing
- Performance metrics

## Indexing GitHub Repositories

### Method 1: Using the REST API

#### Index a Single Repository

```bash
curl -X POST http://localhost:8000/api/vector-db/index \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-github-org",
    "repo": "your-repo-name",
    "branch": "main",
    "collection": "github_repos"
  }'
```

#### Response

```json
{
  "success": true,
  "message": "Successfully indexed repository your-github-org/your-repo-name",
  "stats": {
    "files_processed": 42,
    "documents_created": 156,
    "embeddings_generated": 156
  }
}
```

### Method 2: Using the Frontend UI

1. Navigate to **Integrations Hub** tab
2. Click on **GitHub** integration card
3. Enter repository details:
   - Owner: `your-github-org`
   - Repository: `your-repo-name`
   - Branch: `main` (default)
4. Click **Index Repository**
5. Monitor progress in the activity log

### Method 3: Using Python

```python
import requests

# Index repository
response = requests.post(
    "http://localhost:8000/api/vector-db/index",
    json={
        "owner": "your-github-org",
        "repo": "your-repo-name",
        "branch": "main",
        "collection": "github_repos"
    }
)

result = response.json()
print(f"Indexed {result['stats']['documents_created']} documents")
```

## Re-indexing Existing Repositories

If you need to re-index a repository (e.g., after code changes):

### Option 1: Delete and Re-index

```bash
# 1. Delete existing documents (via API - to be implemented)
curl -X DELETE http://localhost:8000/api/vector-db/repository/{owner}/{repo}

# 2. Re-index
curl -X POST http://localhost:8000/api/vector-db/index \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "your-github-org",
    "repo": "your-repo-name"
  }'
```

### Option 2: Qdrant will automatically update existing points

Qdrant's `upsert` operation automatically:
- Updates existing documents if doc_id matches
- Adds new documents for new files
- Preserves data integrity

Simply run the index command again - it's safe to re-run!

## Verifying Indexing

### Check Collection Stats

```bash
curl http://localhost:8000/api/vector-db/status
```

Response:
```json
{
  "provider": "qdrant",
  "initialized": true,
  "collections": [
    {
      "name": "github_repos",
      "count": 1250,
      "dimension": 768,
      "provider": "qdrant",
      "status": "green"
    }
  ]
}
```

### Test Semantic Search

```bash
curl -X POST http://localhost:8000/api/vector-db/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication middleware",
    "collection": "github_repos",
    "top_k": 5,
    "repository": "your-github-org/your-repo-name"
  }'
```

## Data Persistence

### ✅ Advantages of Qdrant vs In-Memory

| Feature | In-Memory | Qdrant |
|---------|-----------|---------|
| Persistence | ❌ Lost on restart | ✅ Survives restarts |
| Performance | ⚡ Very fast | ⚡ Fast |
| Scalability | ⚠️ RAM limited | ✅ Disk-based |
| Production Ready | ❌ No | ✅ Yes |

### Backup and Restore

#### Backup Qdrant Data

```bash
# Stop Qdrant
docker-compose down

# Backup data
tar -czf qdrant-backup-$(date +%Y%m%d).tar.gz qdrant_storage/

# Restart
docker-compose up -d
```

#### Restore from Backup

```bash
# Stop Qdrant
docker-compose down

# Restore data
tar -xzf qdrant-backup-20241019.tar.gz

# Restart
docker-compose up -d
```

## Troubleshooting

### Qdrant Container Won't Start

```bash
# Check logs
docker-compose logs qdrant

# Common fixes:
# 1. Port conflict
sudo lsof -i :6333
# Kill process or change port in docker-compose.yml

# 2. Permission issues
sudo chown -R $USER:$USER qdrant_storage/

# 3. Corrupted data
docker-compose down -v  # WARNING: Deletes all data!
docker-compose up -d
```

### Indexing Fails

**Error: "Failed to connect to Qdrant"**
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Check environment variable
echo $VECTOR_DB_PROVIDER  # Should be "qdrant"
```

**Error: "GitHub token invalid"**
```bash
# Verify token
echo $GITHUB_TOKEN

# Test GitHub connection
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Slow Indexing

- **Large repositories**: Indexing takes time proportional to file count
- **Rate limits**: GitHub API may throttle requests
- **Solution**: Be patient, monitor logs for progress

## Performance Optimization

### Batch Indexing Multiple Repositories

```python
import requests

repositories = [
    ("org1", "repo1"),
    ("org1", "repo2"),
    ("org2", "repo3"),
]

for owner, repo in repositories:
    print(f"Indexing {owner}/{repo}...")
    response = requests.post(
        "http://localhost:8000/api/vector-db/index",
        json={"owner": owner, "repo": repo}
    )
    print(f"  {response.json()['message']}")
```

### Monitoring Index Health

```bash
# Get collection stats
curl http://localhost:8000/api/vector-db/status | jq '.collections[0]'

# Check Qdrant metrics
curl http://localhost:6333/metrics
```

## Best Practices

1. **Regular Re-indexing**: Set up cron job to re-index active repositories weekly
2. **Monitor Disk Space**: Qdrant data grows with indexed content
3. **Backup Before Major Changes**: Always backup before schema changes
4. **Use Repository Filters**: Filter searches by repository for better results
5. **Test Queries**: Verify search quality after indexing

## Advanced: Custom Collections

Create separate collections for different purposes:

```python
# Create a custom collection
await vector_db.create_collection(
    name="production_repos",
    dimension=768
)

# Index into custom collection
response = requests.post(
    "http://localhost:8000/api/vector-db/index",
    json={
        "owner": "org",
        "repo": "prod-app",
        "collection": "production_repos"
    }
)
```

## Next Steps

- [Vector DB Usage Guide](./VECTOR_DB_USAGE.md) - Complete API reference
- [GitHub-LLM Integration](./FEATURE_CONVERSATIONAL_CONTEXT.md) - AI-powered code queries
- [Architecture Documentation](./replit.md) - System overview

## Support

For issues or questions:
1. Check Qdrant logs: `docker-compose logs qdrant`
2. Check application logs: Check the workflow console
3. Verify configuration in `.env` file
