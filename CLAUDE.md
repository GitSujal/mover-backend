# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MoveHub is a production-grade moving companies marketplace backend built with FastAPI, PostgreSQL, AWS, and UV package manager. It connects verified moving companies with customers through a secure, scalable multi-tenant platform.

## Essential Commands

### Package Management (UV)
```bash
# Install dependencies (10-100x faster than pip)
uv pip install -e ".[dev,test]"

# Or use make command
make install-dev

# Generate/update lock file
uv pip compile pyproject.toml -o requirements.txt --all-extras

# Upgrade all dependencies
make upgrade
```

### Development Server
```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use make command
make dev
```

### Database Management
```bash
# Run all migrations
alembic upgrade head
# Or: make migrate-up

# Create new migration
alembic revision --autogenerate -m "description"
# Or: make migrate-create MSG="description"

# Rollback last migration
alembic downgrade -1
# Or: make migrate-down

# View migration history
alembic history
# Or: make migrate-history

# Reset database (WARNING: destroys all data)
make db-reset
```

### Docker Services
```bash
# Start PostgreSQL + Redis + observability stack
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Build Docker image
docker build -t movehub-api:latest .
```

### Testing
```bash
# Run all tests with coverage (requires 85% minimum)
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html && open htmlcov/index.html

# Run specific test file
pytest tests/test_pricing.py

# Run specific test function
pytest tests/test_pricing.py::test_function_name -v
```

### Code Quality
```bash
# Format code
black app/ tests/
ruff --fix app/ tests/
# Or: make format

# Check code quality (without fixing)
black --check app/ tests/
ruff check app/ tests/
mypy app/
# Or: make lint

# Run all checks (lint + test)
make check
```

## Architecture

### Multi-Tenant Design
- **Row-Level Security (RLS)**: Data isolation enforced at PostgreSQL level using session variables
- Every authenticated request sets `app.current_org_id` and `app.current_user_id` in PostgreSQL
- All database queries automatically filtered by organization context
- Use [RLSSession](app/core/database.py#L258) context manager for automatic RLS setup:
  ```python
  async with RLSSession(org_id="uuid") as session:
      # Queries automatically filtered by org_id
      results = await session.execute(select(Organization))
  ```

### Database Connection Pooling
- **Critical**: Uses singleton pattern with global engine and session factory
- Connections are reused from pool, NOT created per request
- Configuration in [app/core/database.py](app/core/database.py):
  - `pool_size`: Base connections (default: 20)
  - `max_overflow`: Additional connections (default: 10)
  - `pool_recycle`: Recycle after 3600s (prevents stale connections)
  - `pool_pre_ping`: Test connection validity before use
  - `pool_timeout`: Max wait time (30s)
- Testing uses `NullPool` (no pooling overhead)
- Production uses `AsyncAdaptedQueuePool`
- **NEVER** close the engine during request handling - connections return to pool

### Authentication System
- **Dual authentication**: JWT for movers, OTP sessions for customers
- **Movers**: JWT with HTTP-only cookies + refresh tokens ([app/core/security.py](app/core/security.py))
- **Customers**: Session-based OTP authentication (no accounts required)
- Dependencies in [app/api/dependencies.py](app/api/dependencies.py):
  - `get_current_user()`: JWT validation for movers
  - `get_current_customer_session()`: Session validation for customers
  - `require_role()`: Role-based access control
  - `require_approved_organization()`: Organization status check

### Conflict-Free Scheduling
- PostgreSQL **ExcludeConstraint** prevents double-booking ([app/models/booking.py:167](app/models/booking.py#L167))
- Uses `tsrange` with GiST index for efficient overlap detection
- Bookings have `effective_start` and `effective_end` times including commute buffer
- Constraint: No two bookings for the same truck can have overlapping time windows
- This is enforced at database level - application cannot bypass

### Dynamic Pricing Engine
- Extensible rule-based pricing in [app/services/pricing.py](app/services/pricing.py)
- Supports multiple surcharge types:
  - **Stairs**: Per-flight charges (only at locations without elevators)
  - **Special items**: Piano, antiques, fragile items
  - **Time-based**: Weekend, after-hours, holiday multipliers
  - **Distance**: Long-distance surcharges
  - **Custom**: Configurable per-organization rules
- Pricing configuration stored as JSONB in `pricing_configs` table
- All calculations traced with OpenTelemetry

### Observability Stack
- **OpenTelemetry**: Comprehensive tracing, metrics, and logs
- Instrumentation in [app/core/observability.py](app/core/observability.py)
- Metrics exposed at `/metrics` (Prometheus format)
- Traces sent to Jaeger (access at http://localhost:16686)
- All database queries, HTTP requests, and pricing calculations traced
- Structured logging with JSON format and trace correlation

## Key Models

### Database Schema
Located in [app/models/](app/models/):
- **organizations**: Moving companies with verification status
- **users**: Mover accounts with role-based permissions
- **insurance_policies**: Required coverage with expiry tracking
- **trucks**: Fleet with PostGIS location and capacity
- **drivers**: Verified personnel with license information
- **bookings**: Conflict-free scheduling with exclusion constraints
- **pricing_configs**: Extensible JSON rules per organization
- **invoices**: Immutable financial records
- **customer_sessions**: OTP-based sessions for customers

### Base Model
All models inherit from [BaseModel](app/models/base.py) which provides:
- `id`: UUID primary key
- `created_at`: Timestamp with timezone
- `updated_at`: Auto-updating timestamp
- Standard `__repr__` implementation

## Configuration

### Settings Management
- Type-safe settings in [app/core/config.py](app/core/config.py) using Pydantic
- Environment variables from `.env` file (see `.env.example` for template)
- Validation at startup - app will not start with invalid config
- Access via `from app.core.config import settings`

### Critical Configuration
- **Database pooling**: Sized for production load (30 total connections)
- **JWT tokens**: 15min access, 7 day refresh
- **Rate limiting**: 60 requests/minute per IP (Redis-backed)
- **Statement timeout**: 30s max query time (prevents long-running queries)
- **Connection timeout**: 30s max wait for connection from pool

## Services

Located in [app/services/](app/services/):
- **booking.py**: Booking creation with conflict detection
- **pricing.py**: Price calculation with extensible rules
- **payments.py**: Stripe integration for payment processing
- **s3.py**: AWS S3 pre-signed URLs for file uploads
- **redis_cache.py**: Redis caching and rate limiting
- **notifications.py**: Twilio (SMS) and SendGrid (email)

## API Structure

Located in [app/api/routes/](app/api/routes/):
- Routes mounted at `/api/v1` prefix
- **auth.py**: Authentication endpoints (JWT + OTP)
- **bookings.py**: Booking CRUD and availability checks
- OpenAPI docs at `/docs` (only in DEBUG mode)
- Health checks: `/health`, `/health/db`, `/health/redis`

## Testing

### Test Structure
- Tests in [tests/](tests/) directory
- Fixtures in [conftest.py](tests/conftest.py)
- Uses `pytest-asyncio` for async tests
- Test database: `movehub_test` (automatically created/dropped)

### Test Markers
```python
@pytest.mark.unit  # Fast isolated tests
@pytest.mark.integration  # Database/external service tests
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.slow  # Long-running tests
```

### Test Fixtures
- `db_engine`: Test database engine (function-scoped)
- `db_session`: Test database session with rollback
- `client`: AsyncClient with test database override
- `sample_organization_data`: Mock organization data
- `sample_booking_data`: Mock booking data

## Important Patterns

### Database Sessions
```python
# In FastAPI endpoints - use dependency injection
async def endpoint(db: AsyncSession = Depends(get_db)):
    # Session automatically managed (committed/rolled back)
    pass

# Outside FastAPI - use context manager
async with get_db_context() as db:
    # Session auto-commits on success, rolls back on error
    pass

# With RLS context
async with RLSSession(org_id="uuid", user_id="uuid") as db:
    # RLS automatically set/cleared
    pass
```

### Adding New Surcharge Rules
When adding pricing rules, update [app/services/pricing.py](app/services/pricing.py):
1. Add rule type to [SurchargeRule](app/schemas/pricing.py) schema
2. Implement logic in `_apply_surcharge_rule()` method
3. Add span attributes for observability
4. Update pricing config JSON schema

### Authentication Patterns
```python
# Require authenticated mover
async def endpoint(user: User = Depends(get_current_user)):
    pass

# Require specific role
async def endpoint(user: User = Depends(require_role(UserRole.ORG_OWNER))):
    pass

# Require customer session
async def endpoint(session: CustomerSession = Depends(get_current_customer_session)):
    pass
```

## Common Issues

### Migration Conflicts
- Always pull latest before creating migrations
- Review auto-generated migrations carefully (especially for RLS policies)
- Test migrations in both directions (upgrade + downgrade)

### Connection Pool Exhaustion
- Check pool metrics in logs (size, checked_in, checked_out, overflow)
- Ensure sessions are properly closed (use context managers)
- Increase pool size if consistently hitting max_overflow

### Double-Booking Prevention
- Let PostgreSQL handle conflicts - don't try to prevent in application layer
- Catch `IntegrityError` for exclusion constraint violations
- Wrap in `BookingConflictError` with user-friendly message

### Rate Limiting
- Redis-backed, per-IP by default
- Customize in [app/main.py:177](app/main.py#L177)
- Disable with `RATE_LIMIT_ENABLED=false` for testing

## Security Considerations

- **Never log PII**: Customer names, emails, phones masked in traces
- **SQL injection**: Use SQLAlchemy parameters, never string formatting
- **JWT secrets**: Minimum 32 characters, rotate regularly
- **S3 uploads**: Pre-signed URLs with expiration and validation
- **RLS policies**: Always set context for authenticated requests
- **Rate limiting**: Enabled by default (60 req/min per IP)
- **Input validation**: Pydantic schemas validate all inputs

## Development Workflow

1. **Start services**: `docker-compose up -d`
2. **Run migrations**: `make migrate-up`
3. **Start dev server**: `make dev`
4. **Make changes**: Edit code with auto-reload
5. **Run tests**: `pytest`
6. **Format code**: `make format`
7. **Check quality**: `make lint`
8. **Create migration**: `make migrate-create MSG="description"`
9. **Commit changes**: Git workflow

## Deployment

- Docker image built with [Dockerfile](Dockerfile)
- Multi-stage build for minimal image size
- AWS ECS Fargate deployment via CDK (infrastructure/aws-cdk/)
- Environment variables injected via AWS Systems Manager Parameter Store
- Database migrations run automatically on startup
- Health checks at `/health` for load balancer
