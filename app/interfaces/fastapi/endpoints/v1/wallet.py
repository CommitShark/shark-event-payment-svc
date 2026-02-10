from fastapi import APIRouter, Query
from uuid import UUID
from app.domain.dto import PersonalAccountWithSignature
from app.application.dto.base import BaseResponseDTO
from app.application.dto.wallet import (
    ListUserTransactionRequestDto,
    ListUserTransactionResponseDto,
    BalanceDto,
    UpdateTransactionPinRequestDto,
    SaveBankReqDto,
)
from app.application.dto.charge_request import GetChargeResDto
from app.application.mappers.wallet import wallet_to_dto
from ...di import (
    ListUserTransactionUseCaseDep,
    GetBalanceUseCaseDep,
    SetTransactionPinUseCaseDep,
    ResolvePersonalAccountUseCaseDep,
    ListBanksUseCaseDep,
    SaveBankUseCaseDep,
    SubmitWithdrawalUseCaseDep,
)
from ...context import UserContextDep

router = APIRouter(prefix="/v1/wallet", tags=["Wallet"])


@router.get("/balance", response_model=BalanceDto)
async def get_wallet_balance(
    context: UserContextDep,
    use_case: GetBalanceUseCaseDep,
):
    wallet = await use_case.execute(context.user_id)
    return wallet_to_dto(wallet)


@router.get("/transactions", response_model=ListUserTransactionResponseDto)
async def get_transactions(
    context: UserContextDep,
    use_case: ListUserTransactionUseCaseDep,
    page: int = Query(...),
    page_size: int = Query(...),
    ticket_ids: str | None = Query(None),
):
    uuids: list[UUID] = []
    if ticket_ids:
        parts = ticket_ids.split(",")
        for part in parts:
            uuids.append(UUID(part))

    req = ListUserTransactionRequestDto(
        page=page,
        page_size=page_size,
        sort_by="occurred_on",
        user_id=context.user_id,
        ticket_ids=uuids,
    )

    result = await use_case.by_user(req)

    return ListUserTransactionResponseDto(**result.model_dump())


@router.post(
    "/update-transaction-pin",
    response_model=BaseResponseDTO,
)
async def update_transaction_pin(
    use_case: SetTransactionPinUseCaseDep,
    req: UpdateTransactionPinRequestDto,
    context: UserContextDep,
):
    await use_case.execute(context.user_id, req.pin, req.old_pin)
    return BaseResponseDTO(success=True)


@router.get(
    "/resolve-personal-account", response_model=PersonalAccountWithSignature | None
)
async def resolve_personal_account(
    account_number: str,
    bank_code: str,
    use_case: ResolvePersonalAccountUseCaseDep,
):
    account, sig = await use_case.execute(account_number, bank_code)
    return PersonalAccountWithSignature(**account.model_dump(), signature=sig)


@router.get("/banks")
async def list_banks(use_case: ListBanksUseCaseDep):
    return await use_case.execute()


@router.post(
    "/update-bank",
    response_model=BaseResponseDTO,
)
async def update_withdrawal_bank(
    use_case: SaveBankUseCaseDep,
    req: SaveBankReqDto,
    context: UserContextDep,
):
    await use_case.execute(
        req=req,
        user=context.user_id,
    )
    return BaseResponseDTO(success=True)


@router.post("/withdraw", response_model=BaseResponseDTO)
async def submit_withdrawal(
    use_case: SubmitWithdrawalUseCaseDep,
    req: GetChargeResDto,
    context: UserContextDep,
):
    await use_case.execute(
        amount=req.base_amount,
        calculated_charge=req.calculated_charge,
        charge_setting_id=req.charge_setting_id,
        signature=req.signature,
        user_id=str(context.user_id),
        version_id=req.version_id,
        version_number=req.version_number,
    )
    return BaseResponseDTO(success=True)
