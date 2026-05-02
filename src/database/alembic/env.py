import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add src to sys.path to allow imports from internal modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "src"))

from api.core.config import get_settings
from database.table import BaseSQLTable
# Import all models here for autogenerate to work
from modules.accounts.infrastructure.persistence.orm import models as account_models

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
    settings = get_settings()
    url = settings.DATABASE_URL
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
    settings = get_settings()
    
    # Overwrite the sqlalchemy.url from settings
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(settings.DATABASE_URL)
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
