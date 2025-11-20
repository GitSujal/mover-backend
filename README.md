# MoveHub - Production-Grade Moving Companies Marketplace

A secure, scalable, and maintainable **full-stack application** connecting verified moving companies with customers. Built with **Next.js 14 + TypeScript** frontend and **FastAPI** backend, PostgreSQL, Redis, and comprehensive CI/CD.

## 🚀 Features

### Full-Stack
- **Modern Frontend**: Next.js 14 with TypeScript, TailwindCSS, and Server-Side Rendering
- **Type-Safe Integration**: TypeScript types mirror Pydantic models exactly
- **Multi-Step Booking Flow**: 5-step customer journey with real-time validation
- **Responsive UI**: Mobile-first design with TailwindCSS
- **Real-Time Updates**: TanStack Query for optimistic updates and caching

### Backend
- **Multi-tenant Architecture**: Isolated data per organization with Row-Level Security
- **Conflict-Free Scheduling**: PostgreSQL exclusion constraints prevent double-booking
- **Dynamic Pricing Engine**: Extensible surcharge rules (time-based, item-based, distance)
- **Comprehensive Verification**: Insurance policies, driver licenses, truck registrations
- **Dual Authentication**: JWT for movers, OTP sessions for customers
- **Production Observability**: OpenTelemetry traces, metrics, and structured logs
- **AWS-Native**: S3 uploads, SQS queues, RDS PostgreSQL, ElastiCache Redis
- **Type-Safe**: Strict Pydantic v2 models throughout

### Testing & CI/CD
- **24 Backend Tests**: Unit, integration, and E2E with 85%+ coverage target
- **15+ Frontend Tests**: Component and API integration tests
- **6-Stage CI Pipeline**: Linting, type checking, testing, security scanning, builds
- **Docker Compose**: One command to start all 7 services locally

## 🏗️ Architecture

```
                                ┌─────────────┐
                                │  CloudFront │
                                │     CDN     │
                                └──────┬──────┘
                                       │
                        ┌──────────────┴───────────────┐
                        │                              │
                  ┌─────▼──────┐               ┌──────▼──────┐
                  │   Next.js  │               │   FastAPI   │
                  │  Frontend  │◄─────────────▶│   Backend   │
                  │ (Port 3000)│   REST API    │ (Port 8000) │
                  └────────────┘               └──────┬──────┘
                                                      │
                                     ┌────────────────┼────────────────┐
                                     │                │                │
                              ┌──────▼──────┐  ┌─────▼─────┐  ┌──────▼─────┐
                              │  PostgreSQL │  │   Redis   │  │     S3     │
                              │  + PostGIS  │  │  Cache    │  │  Uploads   │
                              └─────────────┘  └───────────┘  └────────────┘
```

### Tech Stack

**Frontend:**
- Next.js 14 (App Router)
- React 18
- TypeScript 5.3 (strict mode)
- TailwindCSS 3.4
- TanStack Query (React Query)
- Zod + React Hook Form
- Axios

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL 16 + PostGIS
- Redis 7.4
- Pydantic v2
- SQLAlchemy 2.0+ (async)
- OpenTelemetry

**Infrastructure:**
- Docker + Docker Compose
- AWS ECS Fargate
- GitHub Actions CI/CD
- Jaeger (tracing)
- Prometheus + Grafana

## 📋 Prerequisites

**Required:**
- Docker + Docker Compose (easiest option)
- **OR** Manual setup:
  - Python 3.11+
  - Node.js 20+ (LTS)
  - PostgreSQL 16+ with PostGIS
  - Redis 7.4+
  - UV (blazing fast Python package manager)

## 🛠️ Quick Start (Recommended)

### Option 1: Docker Compose (Everything in One Command)

```bash
# Clone repository
git clone <repo-url>
cd mover-backend

# Start all services (PostgreSQL + Redis + Backend + Frontend + Observability)
docker compose up

# Access services
# Frontend:   http://localhost:3000
# Backend:    http://localhost:8000
# API Docs:   http://localhost:8000/docs
# Jaeger:     http://localhost:16686
# Grafana:    http://localhost:3001
```

That's it! The application is ready with:
- ✅ Database migrated
- ✅ Seed data loaded (3 companies, 6 trucks, 6 drivers)
- ✅ Backend API running
- ✅ Frontend app running
- ✅ All services connected

### Option 2: Manual Setup (Development)

#### Backend Setup

```bash
# 1. Install UV (10-100x faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install backend dependencies
uv pip install -e ".[dev,test]"

# 3. Start PostgreSQL + Redis
docker-compose up -d postgres redis

# 4. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 5. Run migrations
alembic upgrade head

# 6. Seed database (optional)
python scripts/seed_data.py

# 7. Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

#### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm ci

# 2. Configure environment
cp .env.example .env.local
# Edit NEXT_PUBLIC_API_URL if needed (default: http://localhost:8000)

# 3. Start development server
npm run dev
```

Frontend: `http://localhost:3000`

## 🧪 Testing

### Backend Tests (24 tests)

```bash
# Run all tests with coverage (85% minimum)
pytest

# Run only unit tests (6 tests - fast)
pytest -m unit

# Run integration tests (11 tests - require DB)
pytest -m integration

# Run E2E tests (7 tests - full workflow)
pytest -m e2e

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
```

### Frontend Tests (15+ tests)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run all CI checks (format + lint + type-check + test)
npm run check
```

### Full CI Test Suite (Locally)

```bash
# Backend
black --check app/ tests/
ruff check app/ tests/
mypy app/
pytest --cov=app

# Frontend
cd frontend
npm run format:check
npm run lint
npm run type-check
npm test
```

## 📊 Database Schema

Key tables with production constraints:

- `organizations` - Moving companies with verification status
- `insurance_policies` - Required coverage with expiry tracking
- `trucks` - Fleet with PostGIS location and capacity
- `drivers` - Verified personnel with licenses
- `bookings` - Conflict-free scheduling via exclusion constraints
- `pricing_configs` - Extensible JSON rules per organization
- `invoices` - Immutable financial records

## 🔒 Security

- **Authentication**: JWT with HTTP-only cookies + refresh tokens
- **Authorization**: Row-Level Security enforced at database level
- **Encryption**: TLS 1.3 in transit, AWS KMS at rest
- **PII Protection**: Never logged, masked in traces
- **Rate Limiting**: Redis-backed per-IP/user throttling
- **File Uploads**: Pre-signed S3 URLs with validation

## 📈 Observability

### OpenTelemetry Integration

All components instrumented with:
- **Traces**: Request flow through API → DB → S3
- **Metrics**: Request rates, latency percentiles, error rates
- **Logs**: Structured JSON with trace correlation

### Monitoring Dashboards

```bash
# Access Prometheus metrics
curl http://localhost:8000/metrics

# View traces in Jaeger (if running)
open http://localhost:16686
```

## 🚢 Deployment

### Build Docker Image

```bash
docker build -t movehub-api:latest .
```

### Deploy to AWS ECS

```bash
cd infrastructure/aws-cdk
npm install
cdk deploy --all
```

## ⚡ Why UV?

This project uses **UV** by Astral (creators of Ruff) for package management because it's:

- **10-100x faster** than pip and pip-tools
- **Deterministic** - same dependencies every time
- **Drop-in replacement** - works with existing requirements.txt and pyproject.toml
- **Zero config** - just works out of the box
- **Rust-powered** - written in Rust for maximum performance

```bash
# Example: Install all dependencies in ~1 second (vs ~30s with pip)
uv pip install -e ".[dev,test]"

# Generate lock file
uv pip compile pyproject.toml -o requirements.txt

# Upgrade all dependencies
make upgrade
```

## 🔧 Configuration

### Pricing Engine

Define per-organization pricing rules in `pricing_configs`:

```json
{
  "base_hourly_rate": 150.00,
  "base_mileage_rate": 2.50,
  "minimum_charge": 200.00,
  "surcharge_rules": [
    {
      "type": "stairs",
      "amount": 50.00,
      "per_flight": true
    },
    {
      "type": "weekend",
      "multiplier": 1.25,
      "days": [0, 6]
    }
  ]
}
```

### Row-Level Security

Every request sets organization context:

```sql
SET app.current_org_id = 'uuid-here';
SET app.current_user_id = 'uuid-here';
```

RLS policies enforce data isolation automatically.

## 📚 API Documentation

- **OpenAPI Spec**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **Health Check**: `/health`
- **Metrics**: `/metrics`

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Run tests: `pytest`
3. Format code: `black . && ruff --fix .`
4. Type check: `mypy app/`
5. Commit and push

## 📄 License

Proprietary - All rights reserved

## 🆘 Support

For issues and questions, contact the development team.
