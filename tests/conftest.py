import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Set test environment before importing app
os.environ["ENV_FILE"] = ".env.test"
os.environ["PYTEST_CURRENT_TEST"] = "true"

import os

from app.infrastructure.database import get_db
from app.infrastructure.orm.models import Base
from app.main import app
from config.settings import settings

# Test database URL - usando PostgreSQL como produção
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:Jvc%401702@192.168.11.62:5432/pro_team_care_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

# Test session factory
TestAsyncSession = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Disable autoflush to avoid conflicts
)


@pytest_asyncio.fixture(scope="session")
async def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    # Create tables
    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            print(f"Warning: Creating tables without some indexes due to: {e}")

        # Set up RLS functions and policies for testing
        try:
            # Create RLS functions
            await conn.execute(
                text(
                    """
                CREATE OR REPLACE FUNCTION master.get_current_company_id()
                RETURNS INTEGER AS $$
                BEGIN
                    RETURN COALESCE(NULLIF(current_setting('app.current_company_id', true), '')::INTEGER, 0);
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
            """
                )
            )

            await conn.execute(
                text(
                    """
                CREATE OR REPLACE FUNCTION master.set_current_company_id(company_id INTEGER)
                RETURNS VOID AS $$
                BEGIN
                    PERFORM set_config('app.current_company_id', company_id::TEXT, false);
                END;
                $$ LANGUAGE plpgsql SECURITY DEFINER;
            """
                )
            )

            # Enable RLS on tables
            await conn.execute(
                text("ALTER TABLE master.people ENABLE ROW LEVEL SECURITY;")
            )
            await conn.execute(
                text("ALTER TABLE master.users ENABLE ROW LEVEL SECURITY;")
            )

            # Create policies
            await conn.execute(
                text(
                    """
                CREATE POLICY people_company_isolation_select ON master.people
                FOR SELECT
                USING (company_id = master.get_current_company_id());
            """
                )
            )

            await conn.execute(
                text(
                    """
                CREATE POLICY users_company_isolation_select ON master.users
                FOR SELECT
                USING (company_id = master.get_current_company_id());
            """
                )
            )

            # Admin bypass policies
            await conn.execute(
                text(
                    """
                CREATE POLICY people_admin_bypass ON master.people
                FOR ALL
                TO postgres
                USING (true)
                WITH CHECK (true);
            """
                )
            )

            await conn.execute(
                text(
                    """
                CREATE POLICY users_admin_bypass ON master.users
                FOR ALL
                TO postgres
                USING (true)
                WITH CHECK (true);
            """
                )
            )

        except Exception as e:
            print(f"Warning: RLS setup failed: {e}")

    # Create session
    session = TestAsyncSession()
    try:
        yield session
    finally:
        await session.close()

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(async_session: AsyncSession) -> TestClient:
    """Create test client with overridden dependencies"""

    def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_data():
    """Mock user data for tests"""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "is_active": True,
        "is_superuser": False,
    }


@pytest_asyncio.fixture
async def redis_client():
    """Create mock Redis client for tests"""
    from app.infrastructure.cache.mock_redis import MockRedisClient

    client = MockRedisClient()
    await client.connect()
    yield client
    await client.disconnect()


@pytest.fixture
def authenticated_client(client: TestClient, mock_user_data):
    """Create authenticated test client"""
    # Register user first
    response = client.post("/api/v1/auth/register", json=mock_user_data)
    assert response.status_code == 200

    # Login to get token
    login_data = {
        "username": mock_user_data["email"],
        "password": mock_user_data["password"],
    }
    login_response = client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Add authorization header to client
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(scope="function")
def clean_database():
    """Ensure clean database state for each test"""
    # This fixture can be used to ensure clean state
    yield
    # Cleanup code would go here if needed
