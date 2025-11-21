"""
MoveHub - Production-Grade Moving Companies Marketplace Backend

Main FastAPI application with comprehensive middleware stack:
- OpenTelemetry observability
- CORS
- Rate limiting
- Error handling
- Request logging
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, bookings, driver_assignment, movers, ratings
from app.core.config import settings
from app.core.database import close_db, get_engine
from app.core.observability import initialize_observability, start_prometheus_server
from app.services.booking import BookingConflictError
from app.services.redis_cache import RedisCache

# Initialize logging and observability
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize observability
    initialize_observability(app)

    # Start Prometheus metrics server
    if not settings.DEBUG:
        start_prometheus_server(port=9090)

    # Verify database connection
    try:
        from sqlalchemy import text

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise

    # Verify Redis connection
    try:
        redis = RedisCache()
        await redis._get_cache_client()
        logger.info("✓ Redis connection established")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        # Non-fatal - continue without Redis

    logger.info("✓ Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("✓ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade backend for moving companies marketplace",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Middleware Stack (order matters!)

# 1. Trusted Host (security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.movehub.com", "movehub.com"],
    )

# 2. CORS - Configured for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "Content-Type"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# 3. GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Custom Middleware


@app.middleware("http")
async def add_request_id(request: Request, call_next):  # type: ignore
    """Add unique request ID to all requests."""
    import uuid

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):  # type: ignore
    """Log all incoming requests."""
    import time

    start_time = time.time()

    # Get request details
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        f"{method} {path}",
        extra={
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "request_id": getattr(request.state, "request_id", None),
        },
    )

    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    logger.info(
        f"{method} {path} - {response.status_code} ({duration:.3f}s)",
        extra={
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_seconds": duration,
            "request_id": getattr(request.state, "request_id", None),
        },
    )

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):  # type: ignore
    """Rate limiting middleware."""
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    redis = RedisCache()

    # Check rate limit
    is_allowed = await redis.check_rate_limit(
        key=f"ip:{client_ip}",
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )

    if not is_allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded. Please try again later.",
                "retry_after": 60,
            },
            headers={"Retry-After": "60"},
        )

    return await call_next(request)


# Exception Handlers


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    logger.warning(
        "Validation error",
        extra={
            "errors": exc.errors(),
            "body": exc.body,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(BookingConflictError)
async def booking_conflict_handler(request: Request, exc: BookingConflictError) -> JSONResponse:
    """Handle booking conflicts."""
    logger.warning(f"Booking conflict: {exc}", extra={"path": request.url.path})

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    logger.error(
        f"Database error: {exc}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(
        f"Unexpected error: {exc}",
        exc_info=True,
        extra={"path": request.url.path},
    )

    # Don't expose internal errors in production
    detail = str(exc) if settings.DEBUG else "An unexpected error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


# Health Check Endpoints


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns application status and version.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health/db", tags=["Health"])
async def database_health_check() -> dict:
    """
    Database health check.

    Verifies database connectivity.
    """
    from sqlalchemy import text

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        return {"status": "healthy", "database": "connected"}

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)},
        )


@app.get("/health/redis", tags=["Health"])
async def redis_health_check() -> dict:
    """
    Redis health check.

    Verifies Redis connectivity.
    """
    try:
        redis = RedisCache()
        client = await redis._get_cache_client()
        await client.ping()
        await client.close()

        return {"status": "healthy", "redis": "connected"}

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "redis": "disconnected", "error": str(e)},
        )


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(movers.router, prefix="/api/v1")
app.include_router(ratings.router, prefix="/api/v1")
app.include_router(driver_assignment.router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
