# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MoveHub is a production-grade full-stack moving companies marketplace with a **Next.js 14 TypeScript frontend** and **FastAPI backend**, PostgreSQL, AWS, and UV package manager. It connects verified moving companies with customers through a secure, scalable multi-tenant platform.

**Tech Stack:**
- **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS, TanStack Query, Zod
- **Backend**: FastAPI, PostgreSQL 16 + PostGIS, Redis 7.4, OpenTelemetry
- **Infrastructure**: Docker Compose (7 services), AWS ECS, Multi-platform builds

## Quick Start (Full Stack)

```bash
# Start everything with one command
docker compose up

# Access services
Frontend:   http://localhost:3000
Backend:    http://localhost:8000
API Docs:   http://localhost:8000/docs
Jaeger:     http://localhost:16686
Grafana:    http://localhost:3001
```

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
# Start all services (PostgreSQL + Redis + Frontend + Backend + Observability)
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f frontend

# Build Docker images
docker build -t movehub-api:latest .
docker build -t movehub-frontend:latest ./frontend
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm ci

# Start development server (with hot reload)
npm run dev
# Frontend runs at http://localhost:3000

# Build for production
npm run build

# Start production server
npm start

# Linting and formatting
npm run format:check  # Check formatting with Prettier
npm run format        # Fix formatting
npm run lint          # ESLint
npm run lint:fix      # Fix ESLint issues

# Type checking
npm run type-check    # TypeScript validation

# Testing
npm test              # Run Jest tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage

# Run all checks (same as CI)
npm run check         # format:check + lint + type-check + test
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
# Backend
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

# Frontend
cd frontend
npm run format        # Prettier formatting
npm run lint          # ESLint
npm run type-check    # TypeScript
npm run check         # Run all checks
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

## Frontend Architecture

### Tech Stack
Located in [frontend/](frontend/):
- **Framework**: Next.js 14 with App Router (React 18)
- **Language**: TypeScript 5.3 with strict mode
- **Styling**: TailwindCSS 3.4 with custom components
- **Forms**: React Hook Form + Zod validation
- **API Client**: Axios with interceptors
- **State**: TanStack Query for server state
- **Testing**: Jest + React Testing Library

### Project Structure
```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── page.tsx      # Homepage
│   │   ├── book/         # Booking flow
│   │   └── booking/[id]/ # Booking confirmation
│   ├── components/
│   │   ├── ui/           # Reusable UI components
│   │   └── booking/      # Booking-specific components
│   ├── lib/
│   │   ├── api/          # Type-safe API client
│   │   ├── validations/  # Zod schemas
│   │   └── utils.ts      # Utility functions
│   └── types/            # TypeScript type definitions
├── __tests__/            # Jest tests
└── Configuration files
```

### Key Components

**UI Components** ([frontend/src/components/ui/](frontend/src/components/ui/)):
- **Button**: Multiple variants (default, secondary, outline, destructive), sizes, loading states
- **Input**: Text input with error handling
- **Select**: Dropdown with validation
- **Textarea**: Multi-line input
- **Card**: Container components (Card, CardHeader, CardContent, etc.)
- **Label**: Form labels with required indicator

**Booking Workflow** ([frontend/src/components/booking/](frontend/src/components/booking/)):
- **booking-form.tsx**: Multi-step form controller (5 steps)
- **steps/customer-info-step.tsx**: Step 1 - Name, email, phone
- **steps/pickup-details-step.tsx**: Step 2 - Pickup location, floors, elevator
- **steps/dropoff-details-step.tsx**: Step 3 - Dropoff location
- **steps/move-details-step.tsx**: Step 4 - Date, distance, duration, special items
- **steps/review-step.tsx**: Step 5 - Summary with live price calculation

### Type Safety

**Frontend Types** ([frontend/src/types/booking.ts](frontend/src/types/booking.ts)):
```typescript
export interface BookingCreate {
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  move_date: string;  // ISO 8601
  pickup_address: string;
  // ... 20+ strictly typed fields
}
```

Types mirror backend Pydantic schemas exactly. Any mismatch causes TypeScript compile errors.

**Runtime Validation** ([frontend/src/lib/validations/booking.ts](frontend/src/lib/validations/booking.ts)):
```typescript
export const bookingFormSchema = z.object({
  customer_name: z.string().min(2).max(100),
  customer_email: z.string().email(),
  customer_phone: z.string().regex(/^\d{10}$/),
  move_date: z.string().refine((date) => {
    return new Date(date) >= new Date();
  }, 'Move date must be in the future'),
  // ... complete validation
});
```

### API Integration

**Type-Safe Client** ([frontend/src/lib/api/client.ts](frontend/src/lib/api/client.ts)):
```typescript
// Axios instance with interceptors
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    throw new APIError(error.message, error.response?.status || 0);
  }
);
```

**Booking API** ([frontend/src/lib/api/bookings.ts](frontend/src/lib/api/bookings.ts)):
```typescript
export const bookingAPI = {
  create: async (data: BookingCreate): Promise<BookingResponse> => {
    const response = await apiClient.post('/api/v1/bookings', data);
    return response.data;
  },
  getById: async (id: string): Promise<BookingResponse> => {
    const response = await apiClient.get(`/api/v1/bookings/${id}`);
    return response.data;
  },
  // ... more methods
};
```

### Styling with TailwindCSS

**Configuration** ([frontend/tailwind.config.ts](frontend/tailwind.config.ts)):
- Custom color palette
- Extended spacing and typography
- Custom animations
- Responsive breakpoints

**Utility Function** ([frontend/src/lib/utils.ts](frontend/src/lib/utils.ts)):
```typescript
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Merge Tailwind classes safely
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Frontend Testing

**Component Tests** ([frontend/src/__tests__/components/](frontend/src/__tests__/components/)):
- Button variants and states
- Form inputs with validation
- Loading and error states

**API Client Tests** ([frontend/src/__tests__/lib/](frontend/src/__tests__/lib/)):
- Request/response structure validation
- Error handling
- Type compatibility

**Running Tests**:
```bash
cd frontend
npm test              # Run all tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage report
```

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

### Full-Stack Development

1. **Start all services**: `docker-compose up -d`
2. **Run migrations**: `make migrate-up`
3. **Seed database**: `python scripts/seed_data.py`
4. **Start backend**: `make dev` (port 8000)
5. **Start frontend**: `cd frontend && npm run dev` (port 3000)
6. **Make changes**: Both have auto-reload
7. **Run tests**:
   - Backend: `pytest`
   - Frontend: `cd frontend && npm test`
8. **Format code**:
   - Backend: `make format`
   - Frontend: `cd frontend && npm run format`
9. **Check quality**:
   - Backend: `make lint`
   - Frontend: `cd frontend && npm run check`
10. **Commit changes**: Git workflow

### Backend-Only Development

1. **Start services**: `docker-compose up -d postgres redis`
2. **Run migrations**: `make migrate-up`
3. **Start dev server**: `make dev`
4. **Make changes**: Edit code with auto-reload
5. **Run tests**: `pytest`
6. **Format code**: `make format`
7. **Check quality**: `make lint`
8. **Create migration**: `make migrate-create MSG="description"`

### Frontend-Only Development

1. **Start backend** (or use staging API): Set `NEXT_PUBLIC_API_URL` in `.env.local`
2. **Install dependencies**: `cd frontend && npm ci`
3. **Start dev server**: `npm run dev`
4. **Make changes**: Edit components with hot reload
5. **Run tests**: `npm test`
6. **Format code**: `npm run format`
7. **Check quality**: `npm run check`
8. **Build for production**: `npm run build`

### Adding New Features

**Backend API Endpoint**:
1. Add Pydantic schema in `app/schemas/`
2. Add route in `app/api/routes/`
3. Add service logic in `app/services/`
4. Write tests in `tests/`
5. Run `make check` to verify

**Frontend Component**:
1. Add TypeScript types in `src/types/`
2. Add Zod validation in `src/lib/validations/`
3. Create component in `src/components/`
4. Add API method in `src/lib/api/`
5. Write tests in `src/__tests__/`
6. Run `npm run check` to verify

**Full-Stack Feature**:
1. Design TypeScript/Pydantic types (must match!)
2. Implement backend API
3. Test backend with pytest
4. Implement frontend component
5. Test frontend with Jest
6. Integration test in `tests/test_e2e_integration.py`
7. Run both test suites

## Deployment

### Backend Deployment
- Docker image built with [Dockerfile](Dockerfile)
- Multi-stage build for minimal image size
- AWS ECS Fargate deployment via CDK (infrastructure/aws-cdk/)
- Environment variables injected via AWS Systems Manager Parameter Store
- Database migrations run automatically on startup
- Health checks at `/health` for load balancer

### Frontend Deployment
- Docker image built with [frontend/Dockerfile](frontend/Dockerfile)
- Multi-stage build with Next.js standalone output
- Deployed to AWS ECS or Vercel
- Environment variables: `NEXT_PUBLIC_API_URL`
- Static assets served from CDN (CloudFront)
- SSR with Node.js server

### Docker Compose (All Services)
```bash
# Production-like environment locally
docker-compose up -d

# Services started:
# 1. postgres (PostgreSQL 16 + PostGIS)
# 2. redis (Redis 7.4)
# 3. api (FastAPI backend)
# 4. frontend (Next.js frontend)
# 5. jaeger (Distributed tracing)
# 6. prometheus (Metrics)
# 7. grafana (Dashboards)
```

### CI/CD Pipeline

**6 Jobs Run on Every Push/PR**:
1. **lint-backend**: Black, Ruff, MyPy
2. **lint-frontend**: Prettier, ESLint, TypeScript
3. **test-backend**: Pytest (85% coverage required)
4. **test-frontend**: Jest with coverage
5. **security**: Bandit + Safety scans
6. **build**: Docker images for both services (multi-platform)

**Workflow** ([.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)):
- All linting and tests must pass before Docker builds
- Separate Codecov reports for backend and frontend
- Multi-platform builds (linux/amd64, linux/arm64)
- Automatic deployment on successful main branch builds
