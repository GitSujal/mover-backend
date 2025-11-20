# MoveHub - Production-Grade Moving Companies Marketplace Backend

A secure, scalable, and maintainable backend for connecting verified moving companies with customers, built with FastAPI, PostgreSQL, AWS, and **UV** (10-100x faster than pip).

## 🚀 Features

- **Multi-tenant Architecture**: Isolated data per organization with Row-Level Security
- **Conflict-Free Scheduling**: PostgreSQL exclusion constraints prevent double-booking
- **Dynamic Pricing Engine**: Extensible surcharge rules (time-based, item-based, distance)
- **Comprehensive Verification**: Insurance policies, driver licenses, truck registrations
- **Dual Authentication**: JWT for movers, OTP sessions for customers
- **Production Observability**: OpenTelemetry traces, metrics, and structured logs
- **AWS-Native**: S3 uploads, SQS queues, RDS PostgreSQL, ElastiCache Redis
- **Type-Safe**: Strict Pydantic models throughout

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  CloudFront │─────▶│     ALB      │─────▶│ ECS Fargate │
│     CDN     │      │              │      │  (FastAPI)  │
└─────────────┘      └──────────────┘      └──────┬──────┘
                                                   │
                     ┌─────────────────────────────┼──────────────┐
                     │                             │              │
                ┌────▼────┐                  ┌─────▼─────┐  ┌────▼────┐
                │   RDS   │                  │   Redis   │  │   S3    │
                │PostgreSQL│                  │ElastiCache│  │Uploads  │
                └─────────┘                  └───────────┘  └─────────┘
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+ with PostGIS extension
- Redis 7+
- AWS Account (for production)
- UV (blazing fast Python package manager)

## 🛠️ Local Development Setup

### 1. Install Dependencies

```bash
# Install UV (10-100x faster than pip)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv pip install -e ".[dev,test]"

# Or use make command
make install-dev
```

### 2. Start Services (Docker Compose)

```bash
docker-compose up -d
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your local configuration
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

## 🧪 Testing

```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html
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
