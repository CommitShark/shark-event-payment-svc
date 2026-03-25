from fastapi import APIRouter, Query
from app.application.dto.base import PaginatedResponseDto, PaginatedReqDto
from app.application.dto.transaction import TransactionListDto
from app.interfaces.fastapi.context import AdminUserContextDep
from app.interfaces.fastapi.di import TxnRepoDep

router = APIRouter(prefix="/v1/transactions", tags=["Transactions"])


@router.get(
    "/admin",
    response_model=PaginatedResponseDto[TransactionListDto],
)
async def get_transactions_admin(
    context: AdminUserContextDep,
    txn_repo: TxnRepoDep,
    page: int = Query(...),
    size: int = Query(...),
):
    req = PaginatedReqDto(
        page=page,
        page_size=size,
    )

    transactions, total = await txn_repo.query(
        offset=req.offset,
        limit=size,
    )

    return PaginatedResponseDto[TransactionListDto].create(
        items=[TransactionListDto.from_domain(txn) for txn in transactions],
        page=req.page,
        page_size=req.limit,
        total=total,
    )
