from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.domain.repositories import ITransactionRepository
from app.infrastructure.sqlalchemy.session import get_async_session
from app.infrastructure.sqlalchemy.repositories import (
    SqlAlchemyTransactionRepository,
    SqlAlchemyWalletRepository,
)
from app.infrastructure.grpc import grpc_client
from app.infrastructure.ports import GrpcTicketService, GrpcUserService
from app.domain.ports import IEventBus, IPaymentAdapter
from app.infrastructure.ports.kafka_event_bus import kafka_event_bus
from app.infrastructure.ports.paystack_adapter import get_PaystackAdapter


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


def get_event_bus() -> IEventBus:
    return kafka_event_bus


def get_txn_repo(
    session: AsyncSession,
) -> ITransactionRepository:
    return SqlAlchemyTransactionRepository(session)


def get_ticket_service():
    return GrpcTicketService(grpc_client.get_ticket_grpc_stub())


def get_user_service():
    return GrpcUserService(grpc_client.get_user_grpc_stub())


def get_wallet_repo(
    session: AsyncSession,
):
    return SqlAlchemyWalletRepository(session)


@asynccontextmanager
async def txn_repo_context():
    async for session in get_db():
        repo = get_txn_repo(session)
        yield repo, session


@asynccontextmanager
async def session_context():
    async for session in get_db():
        yield session


def get_IPaymentAdapter() -> IPaymentAdapter:
    return get_PaystackAdapter()
