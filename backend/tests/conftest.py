"""
Pytest configuration and fixtures.
Supports running tests both locally (localhost:5433) and in Docker (postgres:5432).
"""

import os

# Detect if running in Docker by checking for postgres hostname
DB_HOST = os.environ.get("DB_HOST", "postgres" if os.path.exists("/.dockerenv") else "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432" if DB_HOST == "postgres" else "5433")

os.environ["DATABASE_URL"] = f"postgresql+asyncpg://postgres:postgres@{DB_HOST}:{DB_PORT}/fleet"

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import asyncpg

from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@{DB_HOST}:{DB_PORT}/fleet_test"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
async_session_test = async_sessionmaker(engine_test, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def create_test_database():
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres",
        host=DB_HOST,
        port=int(DB_PORT),
        database="postgres"
    )
    try:
        await conn.execute("""
                           SELECT pg_terminate_backend(pg_stat_activity.pid)
                           FROM pg_stat_activity
                           WHERE pg_stat_activity.datname = 'fleet_test'
                             AND pid <> pg_backend_pid()
                           """)
        await conn.execute("DROP DATABASE IF EXISTS fleet_test")
        await conn.execute("CREATE DATABASE fleet_test")
    finally:
        await conn.close()

    yield

    # Cleanup
    await engine_test.dispose()

    conn = await asyncpg.connect(
        user="postgres",
        password="postgres",
        host=DB_HOST,
        port=int(DB_PORT),
        database="postgres"
    )
    try:
        await conn.execute("""
                           SELECT pg_terminate_backend(pg_stat_activity.pid)
                           FROM pg_stat_activity
                           WHERE pg_stat_activity.datname = 'fleet_test'
                             AND pid <> pg_backend_pid()
                           """)
        await conn.execute("DROP DATABASE IF EXISTS fleet_test")
    finally:
        await conn.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_test() as session:
        try:
            yield session
        finally:
            await session.close()

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
