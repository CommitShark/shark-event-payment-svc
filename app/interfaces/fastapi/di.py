from fastapi import Depends, Request
from typing import Annotated, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.sqlalchemy.session import get_async_session
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
from app.domain.ports import IPaymentAdapter, IEventBus
from app.infrastructure.ports import GrpcTicketService
from app.domain.services import ChargeCalculationService
from app.application.use_cases import (
    RequestChargeUseCase,
    CreateCheckoutUseCase,
    VerifyTicketPurchaseTransactionUseCase,
    ListUserTransactionUseCase,
)
from app.infrastructure.grpc import grpc_client


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_IEventBus(
    request: Request,
) -> IEventBus:
    bus = getattr(request.app.state, "event_bus", None)
    if not bus:
        raise RuntimeError("Event bus not initialized")
    return bus


EventBusDep = Annotated[IEventBus, Depends(get_IEventBus)]


def get_payment_adapter(
    request: Request,
) -> IPaymentAdapter:
    adapter = getattr(request.app.state, "paystack_adapter", None)
    if not adapter:
        raise RuntimeError("Paystack adapter not initialized")
    return adapter


PaymentAdapterDep = Annotated[IPaymentAdapter, Depends(get_payment_adapter)]


def get_ITransactionRepository(
    session: DbSession,
) -> ITransactionRepository:
    return SqlAlchemyTransactionRepository(session)


TxnRepoDep = Annotated[ITransactionRepository, Depends(get_ITransactionRepository)]


def get_charge_setting_repository(
    session: DbSession,
) -> IChargeSettingRepository:
    return SqlAlchemyChargeSettingRepository(session)


ChargeSettingRepoDep = Annotated[
    IChargeSettingRepository,
    Depends(get_charge_setting_repository),
]


def get_charge_setting_version_repository(
    session: DbSession,
) -> IChargeSettingVersionRepository:
    return SqlAlchemyChargeSettingVersionRepository(session)


ChargeSettingVersionRepoDep = Annotated[
    IChargeSettingVersionRepository,
    Depends(get_charge_setting_version_repository),
]


def get_RequestChargeUseCase(
    charge_setting_repo: ChargeSettingRepoDep,
    version_repo: ChargeSettingVersionRepoDep,
):
    ticket_stub = grpc_client.get_ticket_grpc_stub()

    charge_calc_service = ChargeCalculationService(
        charge_setting_repo,
        version_repo,
    )
    return RequestChargeUseCase(
        charge_calc_service,
        charge_setting_repo,
        ticket_service=GrpcTicketService(ticket_stub),
    )


RequestChargeUseCaseDep = Annotated[
    RequestChargeUseCase,
    Depends(get_RequestChargeUseCase),
]


def get_CreateCheckoutUseCase(
    payment_adapter: PaymentAdapterDep,
):
    ticket_stub = grpc_client.get_ticket_grpc_stub()
    return CreateCheckoutUseCase(
        ticket_service=GrpcTicketService(ticket_stub),
        payment_adapter=payment_adapter,
    )


CreateCheckoutUseCaseDep = Annotated[
    CreateCheckoutUseCase,
    Depends(get_CreateCheckoutUseCase),
]


def get_VerifyTicketPurchaseTransactionUseCase(
    payment_adapter: PaymentAdapterDep,
    txn_repo: TxnRepoDep,
    event_bus: EventBusDep,
):
    return VerifyTicketPurchaseTransactionUseCase(
        payment_adapter,
        txn_repo,
        event_bus,
    )


VerifyTicketPurchaseTransactionUseCaseDep = Annotated[
    VerifyTicketPurchaseTransactionUseCase,
    Depends(get_VerifyTicketPurchaseTransactionUseCase),
]


def get_ListUserTransactionUseCase(txn_repo: TxnRepoDep):
    return ListUserTransactionUseCase(
        txn_repo=txn_repo,
    )


ListUserTransactionUseCaseDep = Annotated[
    ListUserTransactionUseCase, Depends(get_ListUserTransactionUseCase)
]
