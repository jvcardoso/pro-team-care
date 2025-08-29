from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
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
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Validate connections before use
    connect_args={
        "server_settings": {
            "search_path": settings.db_schema
        }
    }
)

# Create async session factory
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()