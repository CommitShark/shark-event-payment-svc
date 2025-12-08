from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import (
    IChargeSettingRepository,
    IChargeSettingVersionRepository,
    ITransactionRepository,
)
from app.infrastructure.sqlalchemy.repositories import (
    SqlAlchemyChargeSettingRepository,
    SqlAlchemyChargeSettingVersionRepository,
    SqlAlchemyTransactionRepository,
)
from app.application.use_cases import ListTransactionUseCase
from app.infrastructure.sqlalchemy.session import get_async_session


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


@asynccontextmanager
async def session_context():
    async for session in get_db():
        yield session


def get_ITransactionRepository(session: AsyncSession) -> ITransactionRepository:
    return SqlAlchemyTransactionRepository(session)


def get_ListTransactionUseCase(session: AsyncSession):
    return ListTransactionUseCase(get_ITransactionRepository(session))


def get_charge_setting_repo(session: AsyncSession) -> IChargeSettingRepository:
    return SqlAlchemyChargeSettingRepository(session)


def get_charge_setting_version_repo(
    session: AsyncSession,
) -> IChargeSettingVersionRepository:
    return SqlAlchemyChargeSettingVersionRepository(session)
