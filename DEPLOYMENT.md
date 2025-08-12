# BrandGPT Deployment Guide

This document describes how to deploy BrandGPT in a containerized environment.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Host System   │    │   Docker        │    │   Docker        │
│                 │    │   Container     │    │   Container     │
│   Ollama        │◄───┤   BrandGPT      │───►│   Qdrant        │
│   :11434        │    │   :9700         │    │   :6333         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### 1. Host System Requirements
- Docker and Docker Compose installed
- Ollama running on the host system at `localhost:11434`
- Required Ollama models pulled:
  ```bash
  ollama pull hf.co/Qwen/Qwen3-Embedding-8B-GGUF
  ollama pull mistral-small:24b
  ```

### 2. Verify Ollama Setup
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test embedding model
curl http://localhost:11434/api/embed -d '{
  "model": "hf.co/Qwen/Qwen3-Embedding-8B-GGUF",
  "prompt": "test"
}'

# Test LLM model
curl http://localhost:11434/api/generate -d '{
  "model": "mistral-small:24b",
  "prompt": "Hello",
  "stream": false
}'
```

## Deployment Steps

### 1. Clone and Setup
```bash
git clone <repository-url>
cd brandgpt_simple
```

### 2. Configure Environment
```bash
# Copy and customize environment file
cp .env.example .env

# Edit .env if needed - defaults are configured for containerized deployment
# Key settings:
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# QDRANT_URL=http://qdrant:6333
# DATABASE_URL=sqlite:///./data/brandgpt.db
```

### 3. Create Data Directory
```bash
mkdir -p data
chmod 755 data
```

### 4. Deploy with Docker Compose
```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify services are running
docker-compose ps
```

### 5. Verify Deployment
```bash
# Check application health
curl http://localhost:9700/health

# Check API documentation
curl http://localhost:9700/docs

# Test Qdrant connection
curl http://localhost:6337/collections
```

## Service Configuration

### BrandGPT Application
- **Container**: `brandgpt_simple-app-1`
- **Port**: `9700:9700`
- **Database**: SQLite stored in `./data/brandgpt.db`
- **Logs**: `docker-compose logs app`

### Qdrant Vector Database
- **Container**: `brandgpt_simple-qdrant-1`
- **Ports**: `6337:6333` (HTTP), `6338:6334` (gRPC)
- **Data**: Persistent volume `qdrant_data`
- **Logs**: `docker-compose logs qdrant`

### Ollama (Host)
- **Location**: Host system
- **Port**: `11434`
- **Access**: `http://host.docker.internal:11434` from containers

## Monitoring and Maintenance

### Check Service Status
```bash
# View running containers
docker-compose ps

# Check resource usage
docker stats

# View logs
docker-compose logs -f [service_name]
```

### Backup Data
```bash
# Backup SQLite database
cp data/brandgpt.db data/brandgpt.db.backup.$(date +%Y%m%d_%H%M%S)

# Backup Qdrant data
docker-compose exec qdrant qdrant-cli snapshot create
```

### Update Deployment
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or just restart services
docker-compose restart
```

## Scaling and Production Considerations

### 1. Database Scaling
For production, consider migrating from SQLite to PostgreSQL:
```yaml
# Add to docker-compose.yml
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: brandgpt
    POSTGRES_USER: brandgpt
    POSTGRES_PASSWORD: secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### 2. Security
- Change default secret key in production
- Use proper authentication secrets
- Consider reverse proxy (nginx) for HTTPS
- Implement proper firewall rules

### 3. Resource Limits
Add resource limits to docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      memory: 2G
```

### 4. Monitoring
- Add health checks to services
- Implement logging aggregation
- Monitor disk usage for data directory
- Set up alerts for service failures

## Troubleshooting

### Common Issues

1. **Cannot connect to Ollama**
   - Verify Ollama is running on host: `curl localhost:11434/api/tags`
   - Check container can reach host: `docker-compose exec app curl http://host.docker.internal:11434/api/tags`

2. **Qdrant connection failed**
   - Check Qdrant container is running: `docker-compose ps qdrant`
   - Verify ports are accessible: `curl localhost:6337/collections`

3. **Database errors**
   - Ensure data directory exists and is writable
   - Check database file permissions in `./data/`

4. **Out of disk space**
   - Clean Docker images: `docker system prune -a`
   - Check data directory size: `du -sh data/`
   - Consider database cleanup or archiving

### Debug Commands
```bash
# Enter application container
docker-compose exec app /bin/bash

# Check application logs
docker-compose logs app

# Test internal connectivity
docker-compose exec app curl http://qdrant:6333/collections
docker-compose exec app curl http://host.docker.internal:11434/api/tags

# Restart specific service
docker-compose restart app
```