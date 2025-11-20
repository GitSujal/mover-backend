"""
OpenTelemetry observability configuration.
Provides comprehensive tracing, metrics, and logging for production monitoring.
"""

import logging
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio
from prometheus_client import start_http_server

from app.core.config import settings

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure structured logging with trace correlation."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "trace_id=%(otelTraceID)s span_id=%(otelSpanID)s | "
        "%(message)s"
    )

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=log_format,
        handlers=[logging.StreamHandler()],
    )

    # Instrument logging with OpenTelemetry
    LoggingInstrumentor().instrument(set_logging_format=True)

    # Reduce noise from third-party libraries
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)


def setup_tracing() -> TracerProvider:
    """
    Configure distributed tracing with OpenTelemetry.

    Returns:
        TracerProvider: Configured tracer provider
    """
    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    # Configure sampling strategy
    sampler = ParentBasedTraceIdRatio(settings.OTEL_TRACES_SAMPLER_ARG)

    # Create tracer provider
    provider = TracerProvider(resource=resource, sampler=sampler)

    # Add OTLP exporter if endpoint is configured
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP trace exporter configured: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    logger.info("Distributed tracing initialized")
    return provider


def setup_metrics() -> MeterProvider:
    """
    Configure metrics collection with Prometheus and OTLP exporters.

    Returns:
        MeterProvider: Configured meter provider
    """
    # Create resource
    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    # Prometheus metrics reader (pull-based)
    prometheus_reader = PrometheusMetricReader()

    # OTLP metrics exporter (push-based) if endpoint configured
    readers = [prometheus_reader]
    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        otlp_exporter = OTLPMetricExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        otlp_reader = PeriodicExportingMetricReader(otlp_exporter, export_interval_millis=60000)
        readers.append(otlp_reader)
        logger.info(f"OTLP metrics exporter configured: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")

    # Create meter provider
    provider = MeterProvider(resource=resource, metric_readers=readers)

    # Set as global meter provider
    metrics.set_meter_provider(provider)

    logger.info("Metrics collection initialized")
    return provider


def instrument_app(app: "FastAPI") -> None:  # type: ignore # noqa: F821
    """
    Instrument FastAPI application with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=trace.get_tracer_provider(),
        meter_provider=metrics.get_meter_provider(),
        excluded_urls="/health,/metrics",
    )

    logger.info("FastAPI instrumentation complete")


def instrument_database() -> None:
    """Instrument SQLAlchemy and AsyncPG for database tracing."""
    # SQLAlchemy instrumentation
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=trace.get_tracer_provider(),
        enable_commenter=True,  # Add SQL comments with trace context
    )

    # AsyncPG instrumentation
    AsyncPGInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())

    logger.info("Database instrumentation complete")


def instrument_redis() -> None:
    """Instrument Redis for caching and session tracing."""
    RedisInstrumentor().instrument(tracer_provider=trace.get_tracer_provider())
    logger.info("Redis instrumentation complete")


def initialize_observability(app: Optional["FastAPI"] = None) -> None:  # type: ignore # noqa: F821
    """
    Initialize complete observability stack.

    Args:
        app: Optional FastAPI application instance
    """
    # Configure structured logging first
    configure_logging()

    # Setup tracing
    setup_tracing()

    # Setup metrics
    setup_metrics()

    # Instrument database
    instrument_database()

    # Instrument Redis
    instrument_redis()

    # Instrument FastAPI if provided
    if app:
        instrument_app(app)

    logger.info("✓ OpenTelemetry observability initialized successfully")


def start_prometheus_server(port: int = 9090) -> None:
    """
    Start Prometheus metrics HTTP server.

    Args:
        port: Port to expose metrics on (default: 9090)
    """
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.warning(f"Failed to start Prometheus server: {e}")


# Tracer and meter for custom instrumentation
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom metrics
request_counter = meter.create_counter(
    name="movehub.requests.total",
    description="Total number of requests",
    unit="1",
)

booking_counter = meter.create_counter(
    name="movehub.bookings.created",
    description="Total number of bookings created",
    unit="1",
)

pricing_calculation_histogram = meter.create_histogram(
    name="movehub.pricing.calculation.duration",
    description="Time taken to calculate pricing",
    unit="ms",
)

availability_check_histogram = meter.create_histogram(
    name="movehub.availability.check.duration",
    description="Time taken to check availability",
    unit="ms",
)
