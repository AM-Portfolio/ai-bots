# Docker Infrastructure Organization

This directory contains organized Docker configuration files for the AI Bots application.

## Structure

```
docker/
├── docker-compose.yml            # Main compose - runs everything
├── docker-compose.databases.yml  # Database infrastructure only
├── docker-compose.app.yml        # Application services only
├── Dockerfile                    # Backend container build (optimized caching)
├── Dockerfile.frontend           # Frontend container build (optimized caching)
├── .dockerignore                 # Build exclusions
└── .env.docker                   # Docker environment variables
```

## 🚀 Quick Start

### Recommended: Use Clean Build Script

**Windows (PowerShell):**
```powershell
.\scripts\docker-clean-build.ps1
```

**Linux/Mac:**
```bash
./scripts/docker-clean-build.sh
```

The script will:
1. Stop existing containers
2. Let you choose clean level (quick/full/deep)
3. Build both services in parallel (much faster!)
4. Start containers automatically
5. Show status and access URLs

### Manual Build Options

#### Option 1: Quick Build (No Clean)

```bash
# Build and start (uses cache for speed)
docker-compose -f docker-compose.app.yml up -d --build

# View logs
docker-compose -f docker-compose.app.yml logs -f
```

#### Option 2: Clean Build

```bash
# Stop and remove containers
docker-compose -f docker-compose.app.yml down

# Remove old images for fresh build
docker rmi ai-bots-backend:latest ai-bots-frontend:latest

# Build in parallel (faster!)
docker-compose -f docker-compose.app.yml build --parallel

# Start containers
docker-compose -f docker-compose.app.yml up -d
```

### Option 3: Run Databases Only

```bash
# Start databases (MongoDB + Qdrant)
docker-compose -f docker-compose.databases.yml up -d

# Check status
docker-compose -f docker-compose.databases.yml ps

# Stop databases
docker-compose -f docker-compose.databases.yml down
```

### Option 4: Run Full Stack

```bash
# Start everything (databases + app)
docker-compose up -d --build
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

## ⚡ Build Optimization

### Fast Builds with Layer Caching

The Dockerfiles are optimized for maximum caching efficiency:

**Backend (Python):**
1. System dependencies cached (rarely change)
2. Requirements cached (only rebuild if requirements.txt changes)
3. Application code copied last (changes frequently)

**Frontend (Node):**
1. Package files cached (only rebuild if package.json changes)
2. Dependencies cached (npm ci only when package.json changes)
3. Source code copied last (changes frequently)

### Build Time Comparison

| Method | First Build | Subsequent Build | When to Use |
|--------|-------------|------------------|-------------|
| No cache | 8-10 min | 8-10 min | Never recommended |
| With cache | 8-10 min | 30-60 sec | Normal development |
| Parallel build | 5-7 min | 20-40 sec | **Recommended** |

### Parallel Build (Fastest!)

```bash
# Build both services at the same time
docker-compose -f docker-compose.app.yml build --parallel
```

### When to Clean Cache

- **Quick clean** (containers only): Most common, keeps cache
- **Full clean** (build cache): When dependencies change
- **Deep clean** (images + cache): When something is broken

```bash
# Quick clean - removes containers only
docker-compose down

# Full clean - removes build cache
docker builder prune -f

# Deep clean - removes everything
docker-compose down -v
docker rmi ai-bots-backend:latest ai-bots-frontend:latest
docker builder prune -af
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

# Rebuild specific service (with cache)
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
