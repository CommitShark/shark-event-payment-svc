from fastapi import APIRouter, Query

from app.application.dto.wallet import (
    ListUserTransactionRequestDto,
    ListUserTransactionResponseDto,
    BalanceDto,
)
from ...di import ListUserTransactionUseCaseDep, GetBalanceUseCaseDep
from ...context import UserContextDep

router = APIRouter(prefix="/v1/wallet", tags=["Wallet"])


@router.get("/balance", response_model=BalanceDto)
async def get_wallet_balance(
    context: UserContextDep,
    use_case: GetBalanceUseCaseDep,
):
    wallet = await use_case.execute(context.user_id)
    return BalanceDto(
        available=wallet.balance,
        pending=wallet.pending_balance,
    )


@router.get("/transactions", response_model=ListUserTransactionResponseDto)
async def get_transactions(
    context: UserContextDep,
    use_case: ListUserTransactionUseCaseDep,
    page: int = Query(...),
    page_size: int = Query(...),
):
    req = ListUserTransactionRequestDto(
        page=page,
        page_size=page_size,
        sort_by="occurred_on",
        user_id=context.user_id,
    )

    result = await use_case.execute(req)

    return ListUserTransactionResponseDto(**result.model_dump())
