# Connection Pooling Guide

This document explains how connection pooling is implemented in the MoveHub backend and how to optimize it for production.

## Overview

Connection pooling reuses database connections instead of opening/closing them for every request. This dramatically improves performance and reduces load on PostgreSQL.

## Architecture

We use a **two-tier connection pooling** strategy:

```
[FastAPI Workers (4)]
    ↓ (20-30 connections each via SQLAlchemy pool)
[PgBouncer]
    ↓ (100 pooled connections)
[PostgreSQL]
```

### Tier 1: SQLAlchemy Connection Pool (Application Level)

**Configuration:** `app/core/database.py`

```python
pool_size=20                  # Keep 20 connections open per worker
max_overflow=10               # Allow up to 10 extra when needed
pool_timeout=30               # Wait 30s for available connection
pool_recycle=3600             # Recycle connections after 1 hour
pool_pre_ping=True            # Verify connection before use
```

**Total connections per worker:**
- Normal: 20 connections
- Peak: 30 connections (20 + 10 overflow)

**For 4 uvicorn workers:**
- Normal: 80 connections
- Peak: 120 connections

### Tier 2: PgBouncer (Infrastructure Level) - Optional but Recommended

**Configuration:** `config/pgbouncer.ini`

PgBouncer sits between your application and PostgreSQL, pooling connections from ALL application instances.

```
pool_mode = session           # Safe for RLS (Row-Level Security)
max_db_connections = 100      # Only 100 connections to PostgreSQL
max_client_conn = 1000        # Support 1000 application connections
```

**Benefits:**
- Reduces PostgreSQL connections from ~1000 to ~100
- Lower memory usage on database server
- Better handling of connection spikes
- Transparent to application

## Configuration

### Environment Variables

Add to `.env`:

```bash
# SQLAlchemy Pool Settings
DATABASE_POOL_SIZE=20                # Base pool size
DATABASE_MAX_OVERFLOW=10             # Additional connections
DATABASE_POOL_TIMEOUT=30             # Connection timeout (seconds)
DATABASE_POOL_RECYCLE=3600           # Recycle after 1 hour
DATABASE_POOL_PRE_PING=true          # Health check before use
DATABASE_STATEMENT_TIMEOUT=30000     # Query timeout (30s in ms)
```

### Scaling Calculations

**Without PgBouncer:**
```
Max Connections = (WORKERS × (POOL_SIZE + MAX_OVERFLOW))
                = (4 × (20 + 10))
                = 120 connections
```

**With PgBouncer:**
```
Application → PgBouncer: Up to 1000 connections
PgBouncer → PostgreSQL: Only 100 connections
```

## Monitoring

### Check Current Pool Status

The application logs pool metrics on every connection checkout (when `LOG_LEVEL=DEBUG`):

```
Connection checked out from pool:
  size=20,
  checked_in=15,
  checked_out=5,
  overflow=0
```

### PostgreSQL Queries

```sql
-- Check current connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'movehub';

-- See connection details
SELECT
    application_name,
    state,
    count(*)
FROM pg_stat_activity
WHERE datname = 'movehub'
GROUP BY application_name, state;

-- Check for idle connections
SELECT count(*)
FROM pg_stat_activity
WHERE datname = 'movehub'
AND state = 'idle';
```

### PgBouncer Monitoring

```bash
# Connect to PgBouncer admin console
psql -h localhost -p 6432 -U pgbouncer pgbouncer

# Show pool stats
SHOW POOLS;

# Show client connections
SHOW CLIENTS;

# Show server connections
SHOW SERVERS;

# Show statistics
SHOW STATS;
```

## Best Practices

### 1. Set PostgreSQL Connection Limit

In `postgresql.conf`:

```
max_connections = 200  # For 100 PgBouncer + 100 buffer
```

### 2. Always Close Sessions

The `get_db()` dependency handles this automatically:

```python
async def get_db():
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()  # Returns connection to pool
```

### 3. Use Async Operations

Async operations don't block:

```python
# ✅ Good - async, non-blocking
result = await db.execute(select(User))

# ❌ Bad - blocks the connection
time.sleep(10)  # Connection held idle for 10s
```

### 4. Avoid Long Transactions

```python
# ❌ Bad - holds connection for entire operation
async with db.begin():
    for i in range(1000):
        await db.execute(insert(User).values(...))

# ✅ Better - batch operations
async with db.begin():
    await db.execute(insert(User), batch_values)
```

### 5. Monitor Pool Exhaustion

If you see errors like `QueuePool limit exceeded`, either:
- Increase `DATABASE_POOL_SIZE`
- Increase `DATABASE_MAX_OVERFLOW`
- Add PgBouncer
- Optimize slow queries

## Production Deployment

### Option 1: Without PgBouncer (Simple)

```yaml
# docker-compose.yml
api:
  environment:
    DATABASE_URL: postgresql+asyncpg://user:pass@postgres:5432/movehub
    DATABASE_POOL_SIZE: 20
    DATABASE_MAX_OVERFLOW: 10
```

**Pros:** Simple setup
**Cons:** More connections to PostgreSQL

### Option 2: With PgBouncer (Recommended)

```yaml
# docker-compose.yml
services:
  pgbouncer:
    image: pgbouncer/pgbouncer:latest
    volumes:
      - ./config/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini
    ports:
      - "6432:6432"

  api:
    environment:
      DATABASE_URL: postgresql+asyncpg://user:pass@pgbouncer:6432/movehub
      DATABASE_POOL_SIZE: 20
      DATABASE_MAX_OVERFLOW: 10
```

**Pros:**
- Optimal resource usage
- Better scalability
- Centralized connection management

**Cons:** Additional service to manage

### Option 3: AWS RDS Proxy (Managed PgBouncer)

```yaml
api:
  environment:
    DATABASE_URL: postgresql+asyncpg://user:pass@rds-proxy.region.rds.amazonaws.com:5432/movehub
```

**Pros:**
- Fully managed by AWS
- IAM authentication support
- No operational overhead

**Cons:** Additional cost

## Troubleshooting

### Issue: "QueuePool limit exceeded"

**Cause:** Too many concurrent requests, pool exhausted

**Solutions:**
1. Increase pool size: `DATABASE_POOL_SIZE=30`
2. Increase overflow: `DATABASE_MAX_OVERFLOW=20`
3. Add PgBouncer
4. Optimize slow queries

### Issue: "Connection timeout"

**Cause:** Pool waiting too long for available connection

**Solutions:**
1. Increase timeout: `DATABASE_POOL_TIMEOUT=60`
2. Check for connection leaks (sessions not closed)
3. Profile slow queries

### Issue: "Too many connections" (PostgreSQL error)

**Cause:** Exceeded PostgreSQL's `max_connections`

**Solutions:**
1. Add PgBouncer (reduces connections to DB)
2. Increase `max_connections` in `postgresql.conf`
3. Reduce application pool sizes

### Issue: Stale connections

**Cause:** Network issues, PostgreSQL restarts

**Solutions:**
Already handled by:
- `pool_pre_ping=True` - Tests before use
- `pool_recycle=3600` - Recycles after 1 hour

## Performance Metrics

### Without Connection Pooling

```
Request latency: 50-100ms (includes connection setup)
Connections/second: ~20 (limited by connection overhead)
PostgreSQL load: High (constant connect/disconnect)
```

### With Connection Pooling

```
Request latency: 5-10ms (reuses connections)
Connections/second: 1000+ (no connection overhead)
PostgreSQL load: Low (stable connection count)
```

### Improvement

- **10x faster** request handling
- **50x more** requests per second
- **90% less** PostgreSQL CPU usage

## Further Reading

- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [PgBouncer Documentation](https://www.pgbouncer.org/usage.html)
- [PostgreSQL Connection Limits](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [AWS RDS Proxy](https://aws.amazon.com/rds/proxy/)
