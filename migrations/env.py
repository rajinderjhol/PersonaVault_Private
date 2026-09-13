import logging
from logging.config import fileConfig
import sqlalchemy
from sqlalchemy import create_engine
from alembic import context
import sys
import os
from sqlalchemy import pool

# Ensure the project root is in the path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import Base
import app.models
from app.config import Config

# This is the Alembic Config object
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Target metadata for autogenerate
target_metadata = Base.metadata

# Convert async sqlite URL to sync and make path absolute
sync_url = Config.DATABASE_URL.replace('sqlite+aiosqlite:///', 'sqlite:///')
if sync_url.startswith('sqlite:///./'):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sync_url = sync_url.replace('sqlite:///./', f'sqlite:///{project_root}/')

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Create a synchronous engine for migrations
    if context.config.attributes.get('connection'):
        connectable = context.config.attributes.get('connection')
    else:
        connectable = create_engine(sync_url, poolclass=pool.NullPool)

    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

    if isinstance(connectable, sqlalchemy.engine.base.Engine):
        with connectable.connect() as connection:
            do_run_migrations(connection)
    else:
        do_run_migrations(connectable)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
