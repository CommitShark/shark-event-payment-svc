from fastapi import Depends, Request
from typing import Annotated, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.sqlalchemy.session import get_async_session
from app.domain.repositories import (
    IChargeSettingRepository,
    IChargeSettingVersionRepository,
)
from app.infrastructure.sqlalchemy.repositories import (
    SqlAlchemyChargeSettingRepository,
    SqlAlchemyChargeSettingVersionRepository,
)
from app.domain.ports import IPaymentAdapter
from app.infrastructure.ports import GrpcTicketService
from app.domain.services import ChargeCalculationService
from app.application.use_cases import RequestChargeUseCase, CreateCheckoutUseCase
from app.infrastructure.grpc import ticketing_pb2_grpc


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_grpc_ticket_stub(
    request: Request,
) -> ticketing_pb2_grpc.GrpcTicketingServiceStub:
    stub = getattr(request.app.state, "ticket_stub", None)
    if not stub:
        raise RuntimeError("Ticket stub not initialized")
    return stub


GrpcTicketStubDep = Annotated[
    ticketing_pb2_grpc.GrpcTicketingServiceStub,
    Depends(get_grpc_ticket_stub),
]


def get_payment_adapter(
    request: Request,
) -> IPaymentAdapter:
    adapter = getattr(request.app.state, "paystack_adapter", None)
    if not adapter:
        raise RuntimeError("Paystack adapter not initialized")
    return adapter


PaymentAdapterDep = Annotated[IPaymentAdapter, Depends(get_payment_adapter)]


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
    ticket_stub: GrpcTicketStubDep,
):
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
    ticket_stub: GrpcTicketStubDep,
    payment_adapter: PaymentAdapterDep,
):
    return CreateCheckoutUseCase(
        ticket_service=GrpcTicketService(ticket_stub),
        payment_adapter=payment_adapter,
    )


CreateCheckoutUseCaseDep = Annotated[
    CreateCheckoutUseCase,
    Depends(get_CreateCheckoutUseCase),
]
