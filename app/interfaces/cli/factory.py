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
    SqlAlchemyWalletRepository,
)
from app.application.use_cases import (
    ListTransactionUseCase,
    UpdateTransactionStatusUseCase,
)
from app.infrastructure.sqlalchemy.session import get_async_session
from app.infrastructure.ports.kafka_event_bus import kafka_event_bus


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


async def get_UpdateTransactionStatusUseCase(session: AsyncSession):
    if not kafka_event_bus._is_running:
        await kafka_event_bus.connect()

    return UpdateTransactionStatusUseCase(
        SqlAlchemyWalletRepository(session),
        SqlAlchemyTransactionRepository(session),
        kafka_event_bus,
    )


@asynccontextmanager
async def transaction_status_update_use_case():
    async for session in get_db():
        if not kafka_event_bus._is_running:
            await kafka_event_bus.connect()

        use_case = UpdateTransactionStatusUseCase(
            SqlAlchemyWalletRepository(session),
            SqlAlchemyTransactionRepository(session),
            kafka_event_bus,
        )

        yield use_case

        await kafka_event_bus.disconnect()
