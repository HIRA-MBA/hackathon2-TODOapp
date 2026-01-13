import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from app.config.settings import get_settings

settings = get_settings()


def _prepare_async_database_url(url: str) -> tuple[str, dict]:
    """
    Prepare database URL for asyncpg by removing sslmode from query params
    and returning appropriate connect_args for SSL.

    asyncpg doesn't support sslmode as a query parameter - it needs ssl context
    passed via connect_args instead.
    """
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Extract and remove sslmode from query params
    sslmode = query_params.pop("sslmode", [None])[0]

    # Rebuild URL without sslmode
    new_query = urlencode(query_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

    # Configure SSL based on sslmode
    connect_args = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        # Create SSL context for secure connection
        ssl_context = ssl.create_default_context()
        if sslmode == "require":
            # Don't verify certificate for 'require' mode
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_context

    return clean_url, connect_args


# Prepare URL and SSL config for asyncpg
    _database_url, _connect_args = _prepare_async_database_url(settings.database_url)

# Ensure the database URL uses the asyncpg driver
if not _database_url.startswith("postgresql+asyncpg://"):
    _database_url = _database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine for Neon PostgreSQL# Using NullPool since Neon handles connection pooling on their end (transaction pooling)
# This is the recommended approach for serverless PostgreSQL providers
engine = create_async_engine(
    _database_url,
    poolclass=NullPool,  # Let Neon handle pooling
    connect_args=_connect_args,
    echo=settings.environment == "development",
)

# Create async session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database tables (for development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
