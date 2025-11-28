from typing import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from sqlalchemy.schema import MetaData
from app.config import db_config as settings

_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
    return _engine


def get_sessionmaker():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )
    return _SessionLocal


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Proper async context manager for database sessions with full
    transaction handling"""
    session_factory = get_sessionmaker()
    session = session_factory()

    print("Database session created")
    try:
        yield session
        await session.commit()
        print("Transaction committed")
    except Exception as e:
        await session.rollback()
        print(f"Transaction rolled back: {str(e)}")
        raise
    finally:
        await session.close()
        print("Session closed")


async def health_check():
    """Verify database connectivity"""
    try:
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database health check failed: {str(e)}")
        return False
