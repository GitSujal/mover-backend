# Docker Compose Setup

This document explains how to run the entire MoveHub stack with Docker Compose.

## What Gets Started

When you run `docker compose up`, the following services start:

### Core Services
1. **PostgreSQL 16 + PostGIS** (port 5432)
   - Main database with geospatial support
   - Automatically runs migrations on startup
   - Auto-seeds with sample data

2. **Redis 7.4** (port 6379)
   - Caching and session management
   - Persistence enabled

3. **FastAPI Backend** (port 8000)
   - Production-grade Python API
   - Auto-reloads on code changes (development)
   - Runs migrations and seed data automatically

4. **Next.js Frontend** (port 3000)
   - React-based UI
   - Server-side rendering
   - Production optimized build

### Observability Stack
5. **Jaeger** (port 16686)
   - Distributed tracing UI
   - OpenTelemetry collector

6. **Prometheus** (port 9091)
   - Metrics collection
   - Time-series database

7. **Grafana** (port 3001)
   - Metrics visualization
   - Pre-configured dashboards

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ available RAM

### Start Everything
```bash
# Start all services
docker compose up -d

# Watch logs
docker compose logs -f

# Watch specific service
docker compose logs -f frontend
docker compose logs -f api
```

### First Time Setup
The backend automatically:
1. Creates database tables (migrations)
2. Seeds sample data (3 companies, 6 trucks, 6 drivers)

No manual steps needed!

### Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main application UI |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger UI (dev only) |
| **Jaeger** | http://localhost:16686 | Distributed tracing |
| **Grafana** | http://localhost:3001 | Metrics dashboard |
| **Prometheus** | http://localhost:9091 | Metrics database |

### Test the Application

1. **Open the frontend**: http://localhost:3000
2. **Click "Book a Move"**
3. **Fill out the form** - use any valid data
4. **Submit booking** - you'll see confirmation page
5. **Check Jaeger** - see distributed traces at http://localhost:16686

### Stop Services
```bash
# Stop all services (keep data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Development Workflow

### Live Reload
Both frontend and backend support live reload:

```bash
# Start in development mode
docker compose up

# Edit files
# - Backend: Changes in app/ trigger reload
# - Frontend: Changes in frontend/src/ rebuild automatically
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f postgres
```

### Run Commands in Containers

```bash
# Backend shell
docker compose exec api sh

# Run backend tests
docker compose exec api pytest

# Frontend shell
docker compose exec frontend sh

# Database shell
docker compose exec postgres psql -U movehub
```

### Rebuild After Changes

```bash
# Rebuild specific service
docker compose build api
docker compose build frontend

# Rebuild and restart
docker compose up -d --build api
docker compose up -d --build frontend
```

## Service Details

### Backend (FastAPI)
- **Build**: Uses multi-stage Docker build with UV package manager
- **Startup**:
  1. Waits for PostgreSQL to be healthy
  2. Runs `alembic upgrade head` (migrations)
  3. Runs `python scripts/seed_data.py` (sample data)
  4. Starts Uvicorn with auto-reload
- **Volumes**:
  - `./app` → `/app/app` (live reload)
  - `./alembic` → `/app/alembic` (migrations)

### Frontend (Next.js)
- **Build**: Uses Next.js standalone output for minimal image
- **Environment**: Points to backend at `http://localhost:8000`
- **Production mode**: Optimized build with server-side rendering

### PostgreSQL
- **Version**: PostgreSQL 16 with PostGIS 3.4
- **Data**: Persisted in Docker volume `postgres_data`
- **Init**: Runs `scripts/init-db.sql` on first start

### Redis
- **Version**: Redis 7.4 Alpine
- **Persistence**: AOF (Append-Only File) enabled
- **Data**: Persisted in Docker volume `redis_data`

## Environment Variables

### Backend
All configured in docker-compose.yml:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `JWT_SECRET_KEY` - Authentication (change in production!)
- `CORS_ORIGINS` - Allowed origins
- `OTEL_*` - OpenTelemetry configuration

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL (http://localhost:8000)
- `NODE_ENV` - production

## Networking

All services run on the `movehub-network` bridge network:
- Services can communicate using container names
- Frontend → Backend: `http://api:8000` (internal) or `http://localhost:8000` (external)
- Backend → PostgreSQL: `postgres:5432`
- Backend → Redis: `redis:6379`

## Data Persistence

Docker volumes preserve data across restarts:
- `postgres_data` - Database tables and data
- `redis_data` - Redis cache and sessions
- `prometheus_data` - Metrics history
- `grafana_data` - Grafana dashboards

### Reset All Data
```bash
# WARNING: Deletes all data!
docker compose down -v
docker compose up -d
```

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# Change ports in docker-compose.yml if needed
```

### Container Won't Start
```bash
# Check logs
docker compose logs <service-name>

# Check container status
docker compose ps

# Restart specific service
docker compose restart <service-name>
```

### Database Connection Failed
```bash
# Check PostgreSQL is healthy
docker compose ps postgres

# Check logs
docker compose logs postgres

# Verify connection from backend
docker compose exec api python -c "from app.core.database import get_engine; import asyncio; asyncio.run(get_engine())"
```

### Frontend Can't Reach Backend
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS settings in docker-compose.yml
# Ensure CORS_ORIGINS includes frontend URL

# Check frontend environment
docker compose exec frontend env | grep API_URL
```

### Out of Memory
```bash
# Check memory usage
docker stats

# Increase Docker Desktop memory limit
# Docker Desktop → Preferences → Resources → Memory
```

## Production Considerations

This `docker-compose.yml` is for **development**. For production:

1. **Change secrets**:
   - `JWT_SECRET_KEY` - Use strong random string
   - PostgreSQL password
   - Grafana admin password

2. **Remove debug flags**:
   - Set `DEBUG: "false"`
   - Set `ENVIRONMENT: production`
   - Disable auto-reload

3. **Use production images**:
   - Tag and version your images
   - Don't mount source code volumes
   - Use `.env` files for secrets

4. **Configure proper CORS**:
   - Set specific allowed origins
   - Don't use wildcards

5. **Use external databases**:
   - AWS RDS for PostgreSQL
   - AWS ElastiCache for Redis

6. **Add health checks and monitoring**:
   - Configure Prometheus alerts
   - Set up Grafana dashboards
   - Enable log aggregation

## Commands Cheat Sheet

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f

# Restart service
docker compose restart api

# Rebuild and restart
docker compose up -d --build

# Run command in container
docker compose exec api <command>

# Scale service
docker compose up -d --scale api=3

# Remove everything including data
docker compose down -v

# Check status
docker compose ps

# View resource usage
docker stats
```

## Summary

**One command to rule them all:**
```bash
docker compose up
```

This starts:
- ✅ PostgreSQL with sample data
- ✅ Redis for caching
- ✅ FastAPI backend (with migrations)
- ✅ Next.js frontend
- ✅ Full observability stack

**Access the app**: http://localhost:3000

Everything is configured and ready to use! 🚀
