# Docker Deployment Guide

## Quick Start

### 1. Build and Run All Services

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### 2. Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant UI**: http://localhost:6333/dashboard
- **MongoDB**: mongodb://admin:aibotspass@localhost:27017

## Services

### Backend (Python FastAPI)
- Port: 8000
- Healthcheck: http://localhost:8000/health
- Environment: `.env.docker`

### Frontend (React + Vite)
- Port: 3000
- Proxies API requests to backend
- WebSocket support enabled

### Qdrant (Vector Database)
- Ports: 6333 (HTTP), 6334 (gRPC)
- Dashboard: http://localhost:6333/dashboard
- Collection: `code_intelligence`

### MongoDB (Database)
- Port: 27017
- Username: `admin`
- Password: `aibotspass`
- Database: `ai_bots`

## Development Commands

```bash
# Rebuild specific service
docker-compose up --build backend

# View logs for specific service
docker-compose logs -f backend

# Execute commands in container
docker-compose exec backend python -c "print('Hello')"

# Restart a service
docker-compose restart backend

# Check service health
docker-compose ps
```

## Network Architecture

```
┌─────────────────┐
│   Frontend      │  Port 3000
│   (Nginx)       │
└────────┬────────┘
         │
         │ /api → Proxy
         │
┌────────▼────────┐
│   Backend       │  Port 8000
│   (FastAPI)     │
└────┬────────┬───┘
     │        │
     │        └───────────┐
     │                    │
┌────▼─────┐      ┌──────▼──────┐
│  Qdrant  │      │   MongoDB   │
│  :6333   │      │   :27017    │
└──────────┘      └─────────────┘
```

## Environment Variables

The `.env.docker` file contains Docker-specific configurations:

- **QDRANT_HOST=qdrant** - Service name instead of localhost
- **DATABASE_URL** - MongoDB connection string
- **ENVIRONMENT=docker** - Deployment environment

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs backend

# Check service status
docker-compose ps

# Restart with clean state
docker-compose down -v
docker-compose up --build
```

### Connection refused errors
- Ensure all services are healthy: `docker-compose ps`
- Check network connectivity: `docker-compose exec backend ping qdrant`
- Verify environment variables: `docker-compose exec backend env | grep QDRANT`

### Port conflicts
```bash
# Check ports in use
netstat -ano | findstr "8000"

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Map to different host port
```

## Production Deployment

For production, consider:

1. **Use secrets management** instead of plaintext in .env
2. **Add nginx reverse proxy** with SSL
3. **Configure resource limits** in docker-compose.yml
4. **Set up monitoring** (Prometheus, Grafana)
5. **Enable backups** for MongoDB and Qdrant volumes
6. **Use health checks** for orchestration

## Scaling

```bash
# Scale backend instances
docker-compose up --scale backend=3 -d

# Note: Requires load balancer configuration
```
