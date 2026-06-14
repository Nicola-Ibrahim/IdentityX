import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src to sys.path to allow imports from internal modules
BASE_DIR = Path(__file__).resolve().parents[5]
sys.path.append(str(BASE_DIR))

# Import all models here for autogenerate to work
from src.accounts.infrastructure.persistence import tables as account_models  # noqa: F401, E402

from src.shared.infrastructure.database.config import get_db_settings  # noqa: E402
from src.shared.infrastructure.database.table import BaseSQLTable  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseSQLTable.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    db_settings = get_db_settings()
    url = str(db_settings.url)
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
    db_settings = get_db_settings()

    # Overwrite the sqlalchemy.url from settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(db_settings.url)

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
