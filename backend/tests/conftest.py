"""
Shared test fixtures for DataBridge Pipeline.

Uses an independent async SQLite database so tests run fast and don't touch
the real PostgreSQL instance.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.database import Base, get_db
from backend.app.core.security import create_access_token
from backend.app.main import app
from backend.app.models.approval import Approval, ApprovalStatus
from backend.app.models.transfer import (
    Transfer,
    TransferCategory,
    TransferPriority,
    TransferStatus,
)
from backend.app.models.user import User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test_databridge.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_user(db_session: AsyncSession) -> Callable:
    """Factory fixture: call with a role string to create and return a User."""
    created: list[User] = []

    async def _create(role: str = "artist", username: str | None = None) -> User:
        uname = username or f"test_{role}_{len(created)}"
        user = User(
            username=uname,
            display_name=f"Test {role.title()}",
            email=f"{uname}@test.local",
            role=UserRole(role),
            department="Test",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.flush()
        created.append(user)
        return user

    return _create


@pytest_asyncio.fixture
async def auth_headers() -> Callable:
    """Factory: returns auth header dict for a given User object."""

    def _headers(user: User) -> dict[str, str]:
        token = create_access_token(subject=user.username)
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest_asyncio.fixture
async def sample_transfer(db_session: AsyncSession) -> Callable:
    """Factory: create a Transfer with standard approval chain."""

    async def _create(
        artist: User,
        *,
        status: str = "pending_team_lead",
        reference: str | None = None,
        name: str = "Test Transfer",
    ) -> Transfer:
        ref = reference or f"TRF-T{artist.id:04d}"
        transfer = Transfer(
            reference=ref,
            name=name,
            category=TransferCategory.VFX_ASSETS,
            status=TransferStatus(status),
            priority=TransferPriority.NORMAL,
            artist_id=artist.id,
            total_files=0,
            total_size_bytes=0,
            staging_path=f"/tmp/test/{ref}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(transfer)
        await db_session.flush()

        for role in [UserRole.TEAM_LEAD, UserRole.SUPERVISOR, UserRole.LINE_PRODUCER,
                     UserRole.DATA_TEAM, UserRole.IT_TEAM]:
            db_session.add(Approval(
                transfer_id=transfer.id,
                required_role=role,
                status=ApprovalStatus.PENDING,
                created_at=datetime.now(timezone.utc),
            ))
        await db_session.flush()
        return transfer

    return _create
