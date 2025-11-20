"""Alembic environment configuration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import app configuration and models
from app.core.config import settings
from app.models.base import Base

# Import all models to ensure they're registered
from app.models import (  # noqa: F401
    Booking,
    Driver,
    InsurancePolicy,
    Invoice,
    Organization,
    PricingConfig,
    Truck,
    User,
    CustomerSession,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set metadata for autogenerate
target_metadata = Base.metadata

# Override sqlalchemy.url from environment
config.set_main_option("sqlalchemy.url", settings.database_url_sync)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=None,
            # Ignore PostGIS and tiger tables
            include_object=lambda obj, name, type_, reflected, compare_to: (
                False if type_ == "table" and name in (
                    "spatial_ref_sys", "geocode_settings", "geocode_settings_default",
                    "pagc_gaz", "pagc_lex", "pagc_rules", "topology", "layer",
                    "faces", "edges", "addrfeat", "loader_variables", "cousub",
                    "county", "featnames", "state", "place", "zip_state", "zip_lookup_base",
                    "zip_state_loc", "addr", "zcta5", "bg", "tract", "tabblock20"
                ) else True
            )
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
