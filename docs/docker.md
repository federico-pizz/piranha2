# Docker & Docker Compose

## What is Docker?

Docker is a tool that packages applications into **containers** - lightweight, isolated environments that include everything needed to run: code, runtime, libraries, and settings.

### Why Docker?

| Problem | Docker Solution |
|---------|-----------------|
| "Works on my machine" | Same environment everywhere |
| Conflicting dependencies | Each container is isolated |
| Complex setup | One command to start everything |
| Different OS requirements | Containers work on any OS |

### Container vs Virtual Machine

```
┌─────────────────────────────────────────┐
│              Virtual Machines            │
├─────────┬─────────┬─────────┬───────────┤
│  App A  │  App B  │  App C  │           │
├─────────┼─────────┼─────────┤           │
│Guest OS │Guest OS │Guest OS │           │
├─────────┴─────────┴─────────┤           │
│         Hypervisor          │           │
├─────────────────────────────┤           │
│          Host OS            │           │
└─────────────────────────────┘           │
                                          │
┌─────────────────────────────────────────┤
│               Containers                 │
├─────────┬─────────┬─────────┬───────────┤
│  App A  │  App B  │  App C  │           │
├─────────┴─────────┴─────────┤           │
│        Docker Engine        │ ← Shared  │
├─────────────────────────────┤           │
│          Host OS            │           │
└─────────────────────────────┴───────────┘
```

Containers share the host OS kernel → Much lighter than VMs!

---

## Docker Compose

Docker Compose manages **multiple containers** as a single application. Instead of running 4 separate `docker run` commands, you define everything in `docker-compose.yml`.

### Our docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: piranha
      POSTGRES_PASSWORD: yourpassword
      POSTGRES_DB: piranha
    ports:
      - "5432:5432"           # host:container
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U piranha"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  # FastAPI Web Application
  web:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://piranha:yourpassword@db:5432/piranha
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app        # Mount for hot-reload

  # Background Scraper
  scraper:
    build: ./scrapers
    environment:
      - DATABASE_URL=postgresql://piranha:yourpassword@db:5432/piranha
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:              # Named volume for persistence
  redis_data:
```

---

## Key Concepts

### 1. Images vs Containers

- **Image**: Blueprint/template (like a class)
- **Container**: Running instance (like an object)

```bash
# List images
sudo docker images

# List running containers
sudo docker ps

# List all containers (including stopped)
sudo docker ps -a
```

### 2. Ports

```yaml
ports:
  - "8000:8000"
  #   ↑     ↑
  # host  container
```

`8000:8000` means: Access container's port 8000 via host's port 8000.

### 3. Volumes

Volumes persist data outside the container lifecycle:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data  # Named volume
  - ./backend:/app                          # Bind mount (local folder)
```

- **Named volumes**: Managed by Docker, persist between restarts
- **Bind mounts**: Link to host filesystem (for development)

### 4. Networks

Compose creates a network automatically. Containers can reach each other by service name:

```
web → db:5432        (not localhost:5432)
web → redis:6379     (not localhost:6379)
scraper → db:5432
```

### 5. depends_on

Control startup order:

```yaml
web:
  depends_on:
    db:
      condition: service_healthy   # Wait for healthcheck
    redis:
      condition: service_started   # Just wait for start
```

### 6. Healthchecks

Verify a service is actually ready:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U piranha"]
  interval: 5s      # Check every 5 seconds
  timeout: 5s       # Fail if no response in 5s
  retries: 5        # Mark unhealthy after 5 failures
  start_period: 10s # Grace period on startup
```

---

## Essential Commands

### Starting & Stopping

```bash
# Start all services (detached)
sudo docker-compose up -d

# Start with rebuild
sudo docker-compose up -d --build

# Start specific service
sudo docker-compose up -d web

# Stop all services (keeps data)
sudo docker-compose stop

# Stop and remove containers (keeps volumes)
sudo docker-compose down

# Stop and remove everything including data
sudo docker-compose down -v   # ⚠️ Deletes database!
```

### Viewing Logs

```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker-compose logs -f web
sudo docker logs piranha2-web-1 -f

# Last N lines
sudo docker logs piranha2-web-1 --tail 50

# Since time
sudo docker logs piranha2-web-1 --since 5m
sudo docker logs piranha2-web-1 --since 2024-01-01
```

### Managing Containers

```bash
# Restart a service
sudo docker-compose restart web

# Stop a service
sudo docker-compose stop scraper

# Start a stopped service
sudo docker-compose start scraper

# Rebuild and restart
sudo docker-compose up -d --build web
```

### Executing Commands

```bash
# Run command in running container
sudo docker exec -it piranha2-web-1 /bin/bash
sudo docker exec -it piranha2-db-1 psql -U piranha -d piranha

# Run one-off command
sudo docker exec piranha2-web-1 python -c "print('hello')"

# Run new container with command
sudo docker run --rm -it python:3.11 python --version
```

### Inspecting

```bash
# Container details
sudo docker inspect piranha2-web-1

# Check health status
sudo docker inspect piranha2-web-1 | grep -A 10 Health

# Resource usage
sudo docker stats

# Disk usage
sudo docker system df
```

---

## Dockerfile Explained

### Backend Dockerfile

```dockerfile
# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Build Layers & Caching

Docker caches each layer. If a layer hasn't changed, it reuses the cache:

```
1. FROM python:3.11-slim    → Cached (always)
2. RUN apt-get install...   → Cached (rarely changes)
3. COPY requirements.txt    → Cached if unchanged
4. RUN pip install...       → Cached if requirements unchanged
5. COPY . .                 → Rebuilt when code changes
```

**Tip**: Put things that change less at the top!

---

## Troubleshooting

### Permission Denied

```bash
# Option 1: Add yourself to docker group
sudo usermod -aG docker $USER
# Then logout and login

# Option 2: Use sudo
sudo docker-compose up -d
```

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill process
sudo kill <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Container Won't Start

```bash
# Check logs
sudo docker logs piranha2-web-1

# Check container status
sudo docker ps -a

# Rebuild from scratch
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d
```

### Out of Disk Space

```bash
# See disk usage
sudo docker system df

# Clean up unused resources
sudo docker system prune

# Remove all unused images
sudo docker image prune -a

# Nuclear option (removes everything unused)
sudo docker system prune -a --volumes
```

### Container Unhealthy

```bash
# Check health status
sudo docker inspect piranha2-db-1 --format='{{.State.Health.Status}}'

# View health check logs
sudo docker inspect piranha2-db-1 --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

---

## Networking Deep Dive

### Default Network

Compose creates a network named `<project>_default`:

```bash
# List networks
sudo docker network ls

# Inspect network
sudo docker network inspect piranha2_default
```

### DNS Resolution

Containers can reach each other by service name:

```bash
# From web container
sudo docker exec piranha2-web-1 ping db
sudo docker exec piranha2-web-1 ping redis
```

### Exposed vs Published Ports

```yaml
# Exposed: Container-to-container only
expose:
  - "5432"

# Published: Host can access
ports:
  - "5432:5432"
```

---

## Best Practices

### 1. Use .dockerignore

```
# .dockerignore
__pycache__
*.pyc
.git
.env
*.md
```

### 2. Use Multi-Stage Builds (for production)

```dockerfile
# Build stage
FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.11-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### 3. Don't Run as Root (production)

```dockerfile
RUN useradd -m appuser
USER appuser
```

### 4. Use Specific Image Tags

```yaml
# Good
image: postgres:15-alpine

# Bad (can break unexpectedly)
image: postgres:latest
```

### 5. Use Environment Files

```yaml
services:
  web:
    env_file:
      - .env
```
