from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# Create async engine with proper URL handling
def get_database_url() -> str:
    """Get properly formatted database URL for async engine"""
    url = settings.database_url
    
    # Ensure we're using the correct async driver
    if url.startswith("pgsql://"):
        url = url.replace("pgsql://", "postgresql+asyncpg://")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif not url.startswith("postgresql+asyncpg://"):
        # If it's already postgresql+asyncpg, keep it
        pass
    
    return url

engine = create_async_engine(
    get_database_url(),
    echo=False,  # Disabled for production
    future=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Validate connections before use
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