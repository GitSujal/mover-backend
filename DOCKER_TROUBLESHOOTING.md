# Docker Build Troubleshooting Guide

## Common Issue: npm ci Gets Stuck During Frontend Build

### Problem
The `npm ci` command hangs indefinitely during the Docker build process, particularly in the frontend container.

### Root Causes
1. **Network timeouts**: Default npm timeouts are too short for large dependency trees
2. **Alpine Linux compatibility**: Some native modules require additional build tools
3. **Cache issues**: Corrupted npm cache can cause hangs
4. **Memory constraints**: Insufficient Docker memory allocation

### Solutions Implemented

#### 1. Enhanced Dockerfile ([frontend/Dockerfile](frontend/Dockerfile))

**Added build dependencies**:
```dockerfile
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++
```
- `python3`, `make`, `g++`: Required for native module compilation
- `libc6-compat`: Better glibc compatibility in Alpine

**Retry logic**:
```dockerfile
RUN npm ci --prefer-offline --no-audit --loglevel=verbose || \
    (echo "npm ci failed, trying with clean cache..." && \
     npm cache clean --force && \
     npm ci --prefer-offline --no-audit --loglevel=info)
```

#### 2. NPM Configuration ([frontend/.npmrc](frontend/.npmrc))

Created `.npmrc` with extended timeouts:
```
fetch-retry-maxtimeout=600000    # 10 minutes
fetch-retry-mintimeout=100000    # 1.67 minutes
fetch-timeout=600000             # 10 minutes
network-timeout=600000           # 10 minutes
prefer-offline=true              # Use cache when available
```

#### 3. Docker Compose Optimization ([docker-compose.yml](docker-compose.yml))

**Removed obsolete version field**:
```yaml
# Before: version: '3.8'
# After: Removed (docker-compose v2 doesn't need it)
```

**Added healthcheck for frontend**:
```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

**Enabled BuildKit caching**:
```yaml
build:
  cache_from:
    - movehub-frontend:latest
```

## How to Test the Fix

### 1. Clean Build (Recommended)
```bash
# Remove all containers and volumes
docker compose down -v

# Remove old images
docker rmi movehub-frontend:latest || true

# Enable BuildKit for better performance
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Build with verbose output
docker compose build frontend --progress=plain --no-cache

# Start the services
docker compose up -d
```

### 2. Watch Build Progress
```bash
# In another terminal, watch the build logs
docker compose build frontend --progress=plain 2>&1 | tee build.log

# Monitor for these stages:
# - "npm ci --prefer-offline" should complete within 5-10 minutes
# - "npm run build" should complete within 2-3 minutes
```

### 3. Monitor Resource Usage
```bash
# Check Docker resource usage during build
docker stats

# If memory usage is high (>90%), increase Docker memory:
# Docker Desktop -> Settings -> Resources -> Memory (increase to 4GB+)
```

## Alternative Approaches

### Option 1: Use Node.js Standard Image (Instead of Alpine)
If issues persist, switch from `node:20-alpine` to `node:20-slim`:

```dockerfile
# Change line 1 in frontend/Dockerfile:
FROM node:20-slim AS base

# Add required dependencies:
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*
```

**Pros**: Better compatibility, fewer native module issues
**Cons**: Larger image size (~200MB vs ~50MB for Alpine)

### Option 2: Pre-build node_modules Locally
```bash
cd frontend
npm ci
cd ..

# Then build Docker image (it will use existing node_modules)
docker compose build frontend
```

### Option 3: Use npm install instead of npm ci
```dockerfile
# In frontend/Dockerfile, replace:
RUN npm ci --prefer-offline --no-audit --loglevel=verbose

# With:
RUN npm install --prefer-offline --no-audit --loglevel=verbose
```

**Note**: `npm install` is more permissive but less deterministic.

## Debugging Commands

### Check Build Context Size
```bash
# Large build context can slow down builds
cd frontend
du -sh .
du -sh node_modules 2>/dev/null || echo "node_modules not found (good!)"

# Verify .dockerignore is working
cat .dockerignore
```

### Test npm ci Locally
```bash
cd frontend

# Test with Docker run (interactive)
docker run --rm -it \
  -v $(pwd):/app \
  -w /app \
  node:20-alpine \
  sh -c "apk add --no-cache libc6-compat python3 make g++ && npm ci --loglevel=verbose"
```

### Check Network Issues
```bash
# Test npm registry access
docker run --rm node:20-alpine \
  sh -c "npm config get registry && npm ping"

# If behind corporate proxy, add to .npmrc:
# proxy=http://proxy.company.com:8080
# https-proxy=http://proxy.company.com:8080
```

### Build with Different Platforms
```bash
# If on Apple Silicon (M1/M2), try AMD64 build:
docker compose build frontend --platform linux/amd64

# Or explicitly set in docker-compose.yml:
# platform: linux/amd64
```

## Monitoring Build Progress

### Enable BuildKit Progress
```bash
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

docker compose build frontend 2>&1 | tee build.log
```

### Check Build Layers
```bash
# See which layers are cached
docker compose build frontend --progress=plain 2>&1 | grep -E "(CACHED|RUN npm)"

# If "RUN npm ci" is always re-running, check if package.json changed
git status frontend/package*.json
```

### Verify Build Speed Improvements
```bash
# Time the build
time docker compose build frontend --no-cache

# Expected times (on modern hardware):
# - First build (cold cache): 3-10 minutes
# - Rebuild (warm cache): 30-60 seconds
# - Code-only change: 10-20 seconds
```

## Prevention

### 1. Keep Dependencies Updated
```bash
cd frontend

# Update dependencies regularly
npm update
npm outdated

# Regenerate lock file
rm package-lock.json
npm install
```

### 2. Use .dockerignore
Ensure [frontend/.dockerignore](frontend/.dockerignore) includes:
```
node_modules
.next
.git
.env*.local
npm-debug.log*
```

### 3. Regular Cache Cleanup
```bash
# Clean Docker build cache (do monthly)
docker builder prune -af

# Clean dangling images
docker image prune -f

# Nuclear option: clean everything
docker system prune -af --volumes
```

## Success Indicators

After implementing these fixes, you should see:

1. ✅ `npm ci` completes in 2-8 minutes (depending on network)
2. ✅ No timeout errors in build logs
3. ✅ Frontend container starts successfully
4. ✅ Health check passes: `docker compose ps` shows "healthy"
5. ✅ Frontend accessible at http://localhost:3000

## Still Having Issues?

### Collect Diagnostic Information
```bash
# System info
docker version
docker compose version
docker info | grep -A5 "CPUs\|Memory"

# Build logs
docker compose build frontend --progress=plain > build.log 2>&1

# Container logs
docker compose logs frontend > frontend.log 2>&1

# Network test
docker run --rm node:20-alpine npm config get registry
```

### Report Issue
Include the following in your bug report:
1. `build.log` (full build output)
2. `frontend.log` (container logs)
3. Docker version and system info
4. Network configuration (proxy, VPN, etc.)
5. Steps to reproduce

## Reference
- NPM CI documentation: https://docs.npmjs.com/cli/v10/commands/npm-ci
- Docker BuildKit: https://docs.docker.com/build/buildkit/
- Next.js Docker: https://nextjs.org/docs/deployment#docker-image
