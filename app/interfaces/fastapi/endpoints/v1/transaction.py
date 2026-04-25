from fastapi import APIRouter, Query
from typing import Optional
from uuid import UUID
from app.application.dto.base import (
    PaginatedResponseDto,
    PaginatedReqDto,
    BaseResponseDTO,
)
from app.domain.events import TransactionCreatedEvent
from app.application.dto.transaction import (
    TransactionListDto,
    TransactionDetailsDto,
    UpdateTransactionStatusReqDto,
)
from app.application.dto import wallet

from app.interfaces.fastapi.context import AdminUserContextDep
from app.interfaces.fastapi.di import (
    TxnRepoDep,
    UpdateTransactionStatusUseCaseDep,
    EventBusDep,
)

from app.domain.entities.value_objects import (
    TransactionSettlementStatus,
    TransactionType,
)
from app.domain.dto import TransactionFilter


router = APIRouter(prefix="/v1/transactions", tags=["Transactions"])


@router.patch(
    "/admin/{transaction_id}/status",
    response_model=BaseResponseDTO,
)
async def update_transaction_status(
    _: AdminUserContextDep,
    use_case: UpdateTransactionStatusUseCaseDep,
    transaction_id: UUID,
    req: UpdateTransactionStatusReqDto,
):
    await use_case.execute(
        wallet.UpdateTransactionStatusReqDto(
            id=transaction_id,
            status=req.status,
            reason=req.reason,
        )
    )

    return BaseResponseDTO(success=True)


@router.post(
    "/admin/{transaction_id}/settle-ticket-purchase",
    response_model=BaseResponseDTO,
)
async def verify_transaction(
    _: AdminUserContextDep,
    transaction_id: UUID,
    repo: TxnRepoDep,
    event_bus: EventBusDep,
):
    transaction = await repo.get_by_id(transaction_id)
    if (
        transaction.transaction_type == "purchase"
        and transaction.resource == "ticket"
        and transaction.settlement_status == "pending"
    ):
        await event_bus.publish(TransactionCreatedEvent.create(transaction))
    else:
        print(f"settle-ticket-purchase: Invalid Transaction")
    return BaseResponseDTO(success=True)


@router.get(
    "/admin",
    response_model=PaginatedResponseDto[TransactionListDto],
)
async def get_transactions_admin(
    context: AdminUserContextDep,
    txn_repo: TxnRepoDep,
    page: int = Query(...),
    size: int = Query(...),
    status: Optional[TransactionSettlementStatus] = Query(None),
    type: Optional[TransactionType] = Query(None),
):
    req = PaginatedReqDto(
        page=page,
        page_size=size,
    )

    transactions, total = await txn_repo.query(
        offset=req.offset,
        limit=size,
        filter=TransactionFilter(
            status=status,
            type=type,
        ),
    )

    return PaginatedResponseDto[TransactionListDto].create(
        items=[TransactionListDto.from_domain(txn) for txn in transactions],
        page=req.page,
        page_size=req.limit,
        total=total,
    )


@router.get(
    "/admin/{transaction_id}",
    response_model=TransactionDetailsDto,
)
async def get_transaction_detail_admin(
    context: AdminUserContextDep,
    txn_repo: TxnRepoDep,
    transaction_id: UUID,
):
    transaction = await txn_repo.get_by_id(transaction_id)
    return TransactionDetailsDto.from_domain(transaction)
