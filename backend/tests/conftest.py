"""Pytest configuration — dedicated test DB and schema setup before app imports."""

from __future__ import annotations

import asyncio
import os

# Use a separate database from dev/prod data (must run before settings are cached).
os.environ.setdefault("POSTGRES_TEST_DB", "riskdb_test")
os.environ["POSTGRES_DB"] = os.environ["POSTGRES_TEST_DB"]

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings

get_settings.cache_clear()
settings = get_settings()


def _ensure_test_database_exists() -> None:
    import psycopg

    maintenance_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
    )
    db_name = settings.POSTGRES_DB

    with psycopg.connect(maintenance_url, autocommit=True) as conn:
        row = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,),
        ).fetchone()
        if row is None:
            conn.execute(f'CREATE DATABASE "{db_name}"')


_ensure_test_database_exists()

# Point the application (including the evaluation worker) at the test database.
import app.core.db as db_module

test_engine = create_async_engine(
    settings.sqlalchemy_database_uri_async,
    pool_pre_ping=True,
)
db_module.engine = test_engine
db_module.AsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

from app.core.db import get_async_session
from app.main import app
from app.models import Business, RiskEvaluation  # noqa: F401


async def _recreate_schema() -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def fast_evaluation(monkeypatch):
    monkeypatch.setattr(
        "app.services.evaluation_worker.settings.RISK_EVALUATION_DELAY_SECONDS",
        0,
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def test_database_schema():
    """Drop and recreate all tables once per test run on the test database."""
    await _recreate_schema()
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    """Reset rows between tests without touching the dev database."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(text("TRUNCATE risk_evaluation, business CASCADE"))
        await session.commit()
    yield


@pytest_asyncio.fixture
async def db_session():
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
