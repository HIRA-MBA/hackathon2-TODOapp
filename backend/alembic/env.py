import asyncio
import ssl
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from alembic import context

# Import all models to ensure they are registered with SQLModel
from app.models.task import Task  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.chatkit_session import ChatkitSession  # noqa: F401
from app.config.settings import get_settings

config = context.config
settings = get_settings()

# Set the database URL from settings (convert to asyncpg driver, handle sslmode)
_raw_url = settings.database_url
_needs_ssl = "sslmode=require" in _raw_url
db_url = _raw_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
if not db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

# Tables managed by Better Auth - exclude from autogenerate
EXCLUDED_TABLES = {"user", "session", "account", "verification", "jwks"}


def include_object(object, name, type_, reflected, compare_to):
    """Filter out Better Auth tables from autogenerate."""
    if type_ == "table" and name in EXCLUDED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connect_args = {}
    if _needs_ssl:
        ssl_context = ssl.create_default_context()
        connect_args["ssl"] = ssl_context

    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
