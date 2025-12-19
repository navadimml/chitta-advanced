"""
Pytest configuration and fixtures for Chitta tests.

Provides:
- Database session fixtures (in-memory SQLite)
- Auth service fixtures
- Test user fixtures
- FastAPI test client
"""

import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"

from app.db.base import Base
from app.db.repositories import UnitOfWork
from app.services.auth import AuthService, TokenService, get_token_service
from app.main import app


# ============================================================================
# Event Loop Fixture
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create a fresh in-memory database for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def uow(async_session) -> AsyncGenerator[UnitOfWork, None]:
    """Create a UnitOfWork with the test session."""
    # Pass session to constructor - repositories are initialized lazily via properties
    uow = UnitOfWork(session=async_session)
    yield uow


# ============================================================================
# Auth Fixtures
# ============================================================================

@pytest.fixture
def token_service() -> TokenService:
    """Get token service instance."""
    return get_token_service()


@pytest_asyncio.fixture
async def auth_service(uow) -> AuthService:
    """Create auth service with test UoW."""
    return AuthService(uow)


@pytest_asyncio.fixture
async def test_user(auth_service, uow):
    """Create a test user and return user data with credentials."""
    email = f"test-{uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    display_name = "Test User"

    result = await auth_service.register(
        email=email,
        password=password,
        display_name=display_name,
        require_email_verification=False,
    )

    await uow.commit()

    return {
        "user": result.user,
        "email": email,
        "password": password,
        "display_name": display_name,
    }


@pytest_asyncio.fixture
async def authenticated_user(auth_service, test_user, uow):
    """Create a test user and login, returning user with tokens."""
    result = await auth_service.login(
        email=test_user["email"],
        password=test_user["password"],
    )

    await uow.commit()

    return {
        **test_user,
        "tokens": result.tokens,
        "access_token": result.tokens.access_token,
        "refresh_token": result.tokens.refresh_token,
    }


# ============================================================================
# API Test Client Fixtures
# ============================================================================

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(authenticated_user) -> dict:
    """Get authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {authenticated_user['access_token']}"}
