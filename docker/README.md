# Docker Infrastructure Organization

This directory contains organized Docker configuration files for the AI Bots application.

## Structure

```
docker/
├── docker-compose.yml            # Main compose - runs everything
├── docker-compose.databases.yml  # Database infrastructure only
├── docker-compose.app.yml        # Application services only
├── Dockerfile                    # Backend container build
├── Dockerfile.frontend           # Frontend container build
├── .dockerignore                 # Build exclusions
└── .env.docker                   # Docker environment variables
```

## Quick Start

### Option 1: Run Everything (Recommended)

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

### Option 2: Run Databases Only

```bash
# Start databases (MongoDB + Qdrant)
docker-compose -f docker-compose.databases.yml up -d

# Check status
docker-compose -f docker-compose.databases.yml ps

# Stop databases
docker-compose -f docker-compose.databases.yml down
```

### Option 3: Run Application Only

**Prerequisites:** Databases must be running first!

```bash
# Start application (backend + frontend)
docker-compose -f docker-compose.app.yml up -d

# Check status
docker-compose -f docker-compose.app.yml ps

# Stop application
docker-compose -f docker-compose.app.yml down
```

## Service Endpoints

| Service  | Internal Port | External Port | Access URL                          |
|----------|---------------|---------------|-------------------------------------|
| Frontend | 3000          | 4000          | http://localhost:4000               |
| Backend  | 8000          | 9000          | http://localhost:9000               |
| Qdrant   | 6333          | 6335          | http://localhost:6335/dashboard     |
| MongoDB  | 27017         | 27018         | mongodb://localhost:27018           |

## Port Configuration

All ports are configurable via `.env.docker`:

```bash
BACKEND_PORT=9000
FRONTEND_PORT=4000
QDRANT_HTTP_PORT=6335
QDRANT_GRPC_PORT=6336
MONGODB_PORT=27018
```

## Network Architecture

All services communicate via the `ai-bots-network` bridge network:

```
┌─────────────────────────────────────────────┐
│         ai-bots-network (bridge)            │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Frontend │→ │ Backend  │→ │  Qdrant  │  │
│  │  :3000   │  │  :8000   │  │  :6333   │  │
│  └──────────┘  └─────┬────┘  └──────────┘  │
│                      │                      │
│                      ↓                      │
│                ┌──────────┐                 │
│                │ MongoDB  │                 │
│                │  :27017  │                 │
│                └──────────┘                 │
└─────────────────────────────────────────────┘
```

## Development Workflow

### 1. Initial Setup

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Wait for health checks
docker-compose ps
```

### 2. Database-First Development

```bash
# Start only databases
docker-compose -f docker-compose.databases.yml up -d

# Develop locally, connecting to Docker databases
# Backend: QDRANT_HOST=localhost, QDRANT_PORT=6335
# MongoDB: mongodb://admin:aibotspass@localhost:27018/ai_bots
```

### 3. Full Stack Development

```bash
# Start everything
docker-compose up -d

# Rebuild specific service
docker-compose up -d --build backend

# View specific service logs
docker-compose logs -f backend
```

## Volume Management

### Persistent Data

- `qdrant_storage` - Vector database data
- `mongodb_data` - MongoDB database files
- `mongodb_config` - MongoDB configuration

### Backup Volumes

```bash
# Backup Qdrant data
docker run --rm -v ai-bots_qdrant_storage:/data -v $(pwd):/backup alpine tar czf /backup/qdrant-backup.tar.gz -C /data .

# Backup MongoDB data
docker run --rm -v ai-bots_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz -C /data .
```

### Clean Slate

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Rebuild from scratch
docker-compose up -d --build
```

## Troubleshooting

### Check Service Health

```bash
# All services
docker-compose ps

# Specific service logs
docker-compose logs backend

# Follow logs
docker-compose logs -f
```

### Network Issues

```bash
# Inspect network
docker network inspect ai-bots-network

# Check connectivity
docker-compose exec backend ping qdrant
docker-compose exec backend ping mongodb
```

### Rebuild Without Cache

```bash
# Rebuild specific service
docker-compose build --no-cache backend

# Rebuild everything
docker-compose build --no-cache
```

### Port Conflicts

If ports are already in use:

1. Edit `.env.docker` to change port numbers
2. Restart services: `docker-compose up -d`

## Production Considerations

- [ ] Use secrets management instead of `.env.docker`
- [ ] Add SSL/TLS with nginx reverse proxy
- [ ] Configure resource limits in compose files
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Enable automated backups for volumes
- [ ] Use health checks for orchestration
- [ ] Implement log aggregation
- [ ] Add security scanning for images

## Advanced Usage

### Multi-File Composition

Combine multiple compose files:

```bash
# Databases + custom overrides
docker-compose -f docker-compose.databases.yml -f docker-compose.custom.yml up -d
```

### Scaling Services

```bash
# Scale backend instances (requires load balancer)
docker-compose up -d --scale backend=3
```

### Environment-Specific Configs

```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```
