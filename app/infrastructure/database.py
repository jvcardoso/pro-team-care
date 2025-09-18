from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings


# Create async engine with proper URL handling
def get_database_url() -> str:
    """Get properly formatted database URL with schema support"""
    # Use the database_url_with_schema property which includes schema parameter
    return settings.database_url_with_schema


engine = create_async_engine(
    settings.database_url,  # Use basic URL without schema parameter
    echo=False,  # Disabled for production
    future=True,
    pool_size=10,  # Reduced pool size to avoid conflicts
    max_overflow=5,  # Allow some overflow connections
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_timeout=30,  # Connection timeout
    connect_args={
        "server_settings": {"search_path": settings.db_schema},
        "command_timeout": 60,  # Command timeout in seconds
        "statement_cache_size": 0,  # Disable statement cache to avoid conflicts
        "prepared_statement_cache_size": 0,  # Disable prepared statement cache
    },
)

# Create async session factory using the new async_sessionmaker
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Disable autoflush to avoid conflicts
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()  # Auto-commit mudanças
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
