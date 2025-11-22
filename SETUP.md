# MoveHub Setup Guide

This guide will help you set up and run the MoveHub application with real data.

## Prerequisites

- Python 3.13+
- Node.js 18+
- PostgreSQL 16+ with PostGIS extension
- Redis 7.4+
- Docker & Docker Compose (optional, for easier setup)

## Quick Start with Docker Compose

The easiest way to run the full application is using Docker Compose:

```bash
# Start all services (PostgreSQL, Redis, API, Frontend, Observability stack)
docker compose up -d

# Check logs
docker compose logs -f api
docker compose logs -f frontend
```

Access the services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Jaeger: http://localhost:16686
- Grafana: http://localhost:3001

## Manual Setup

If you prefer to run services manually:

### 1. Backend Setup

#### Install Dependencies

```bash
# Using UV package manager (10-100x faster than pip)
uv pip install -e ".[dev,test]" --system

# Or using make
make install-dev
```

#### Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and configure database connection
nano .env
```

Required environment variables:
```env
DATABASE_URL=postgresql+asyncpg://movehub:changeme@localhost:5432/movehub
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-min-32-characters
```

#### Start PostgreSQL and Redis

If using Docker:
```bash
docker compose up -d postgres redis
```

Or install locally:
- PostgreSQL: https://www.postgresql.org/download/
- Redis: https://redis.io/download

#### Run Database Migrations

```bash
# Run migrations to create tables
alembic upgrade head

# Or using make
make migrate-up
```

#### Seed the Database

This is **crucial** - without seeding, the frontend will show empty states:

```bash
# Seed database with sample organizations, trucks, drivers, etc.
python scripts/seed_data.py
```

**Important:** After seeding, note the Organization IDs printed:
```
Sample Organizations:
  - Bay Area Movers (550e8400-e29b-41d4-a716-446655440000)
  - Golden Gate Moving Co (...)
  - Oakland Express Movers (...)
```

Copy one of these IDs for use in the frontend configuration.

#### Start the Backend

```bash
# Start with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using make
make dev
```

### 2. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm ci
```

#### Configure Environment

```bash
# Create environment file
cp .env.local.example .env.local

# Edit .env.local
nano .env.local
```

Update with your configuration:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ORG_ID=550e8400-e29b-41d4-a716-446655440000
```

**Note:** Replace `NEXT_PUBLIC_ORG_ID` with one of the Organization IDs from the seed script output.

#### Start the Frontend

```bash
# Development mode with hot reload
npm run dev

# The frontend will be available at http://localhost:3000
```

## Verifying the Setup

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

curl http://localhost:8000/health/db
# Should return database connection status

curl http://localhost:8000/health/redis
# Should return Redis connection status
```

### 2. Check API Docs

Visit http://localhost:8000/docs to see the interactive API documentation.

### 3. Test API Endpoints

```bash
# List organizations
curl http://localhost:8000/api/v1/movers/trucks

# List drivers
curl http://localhost:8000/api/v1/movers/drivers

# Get analytics (replace ORG_ID)
curl "http://localhost:8000/api/v1/analytics/organization/550e8400-e29b-41d4-a716-446655440000/dashboard?start_date=2024-01-01T00:00:00Z&end_date=2025-12-31T23:59:59Z"
```

### 4. Access Frontend

1. Open http://localhost:3000 in your browser
2. Navigate to the mover dashboard at http://localhost:3000/mover
3. You should see:
   - **Dashboard:** Real analytics data (revenue, bookings, fleet status)
   - **Jobs & Schedule:** List of bookings (empty initially, until you create bookings)
   - **Fleet:** List of trucks and drivers from seed data
   - **Analytics:** Comprehensive dashboard with metrics
   - **Invoices:** Invoice management (empty initially)
   - **Support:** Support tickets (empty initially)

## Creating Test Bookings

To populate the dashboard with booking data:

### Option 1: Using the Frontend

1. Go to http://localhost:3000/book
2. Fill out the booking form
3. Submit to create a booking

### Option 2: Using the API

```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "customer_phone": "4155551234",
    "move_date": "2025-12-01T09:00:00Z",
    "pickup_address": "123 Market St",
    "pickup_city": "San Francisco",
    "pickup_state": "CA",
    "pickup_zip_code": "94102",
    "pickup_floor_number": 3,
    "pickup_has_elevator": false,
    "dropoff_address": "456 Mission St",
    "dropoff_city": "Oakland",
    "dropoff_state": "CA",
    "dropoff_zip_code": "94601",
    "dropoff_floor_number": 1,
    "dropoff_has_elevator": true,
    "distance_miles": 12.5,
    "estimated_duration_hours": 4,
    "special_items": ["piano", "artwork"]
  }'
```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:

1. Ensure PostgreSQL is running:
   ```bash
   docker compose ps postgres
   # Or: systemctl status postgresql
   ```

2. Check database exists:
   ```bash
   psql -U movehub -d movehub -c "\dt"
   ```

3. Verify credentials in `.env` match your PostgreSQL setup

### Seed Script Fails

If seeding fails:

1. Ensure migrations have run: `alembic upgrade head`
2. Check database connection
3. Clear existing data if needed:
   ```bash
   make db-reset  # WARNING: Destroys all data
   alembic upgrade head
   python scripts/seed_data.py
   ```

### Frontend Shows Empty States

This is expected if:
- Database hasn't been seeded
- Backend is not running
- Wrong `NEXT_PUBLIC_ORG_ID` in frontend `.env.local`

Solutions:
1. Run seed script: `python scripts/seed_data.py`
2. Verify backend is running: `curl http://localhost:8000/health`
3. Check browser console for API errors (F12)
4. Verify `NEXT_PUBLIC_ORG_ID` matches a seeded organization

### CORS Errors

If you see CORS errors in the browser console:

1. Check that `NEXT_PUBLIC_API_URL` in frontend `.env.local` matches the backend URL
2. Ensure backend is configured to allow the frontend origin
3. Backend should allow `http://localhost:3000` by default in development

## Production Deployment

For production deployment:

1. Set `ENVIRONMENT=production` in backend `.env`
2. Use strong `JWT_SECRET_KEY` (min 32 characters)
3. Configure production database and Redis URLs
4. Build frontend: `cd frontend && npm run build`
5. Use Docker images or deploy to AWS ECS (see `infrastructure/aws-cdk/`)
6. Set up SSL/TLS certificates
7. Configure environment variables in production
8. DO NOT use seed data in production - create real data through the application

## Development Workflow

1. **Start services:** `docker compose up -d` (or manually start backend + frontend)
2. **Make changes:** Edit code with auto-reload enabled
3. **Run tests:**
   - Backend: `pytest`
   - Frontend: `cd frontend && npm test`
4. **Check code quality:**
   - Backend: `make lint`
   - Frontend: `cd frontend && npm run check`
5. **Create migration:** `alembic revision --autogenerate -m "description"`
6. **Commit changes:** Git workflow

## Additional Resources

- [CLAUDE.md](CLAUDE.md) - Comprehensive project documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when backend is running)
- [Architecture Overview](CLAUDE.md#architecture) - Multi-tenant design, auth, pricing
- [Testing Guide](CLAUDE.md#testing) - Test structure and best practices
