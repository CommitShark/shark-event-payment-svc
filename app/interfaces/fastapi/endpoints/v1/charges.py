from fastapi import APIRouter, Query
from decimal import Decimal
from typing import Optional
from app.application.dto.charge_request import (
    ChargeDto,
    GetChargeReqDto,
    GetChargeResDto,
)

from app.interfaces.fastapi.context import UserContextDep, ProtectedDep
from app.interfaces.fastapi.di import RequestChargeUseCaseDep

router = APIRouter(prefix="/v1/charges", tags=["Charges"])


@router.post(
    "/ticket-purchase",
    response_model=GetChargeResDto,
)
async def get_ticket_type_charge(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: RequestChargeUseCaseDep,
    req: GetChargeReqDto,
):
    charges, sig = await use_case.ticket_charge(
        user_id=str(context.user_id),
        ticket_type_id=str(req.ticket_type_id),
        quantity=req.quantity,
        extras=req.extras,
        occurrence_id=req.occurrence_id,
        event_id=req.event_id,
    )

    return GetChargeResDto(
        charges=[ChargeDto.model_validate(c) for c in charges],
        signature=sig,
    )


@router.get("/instant-withdrawal", response_model=Optional[ChargeDto])
async def get_instant_withdrawal_charge(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: RequestChargeUseCaseDep,
    amount: Decimal = Query(...),
):
    result = await use_case.execute(
        user_id=str(context.user_id),
        charge_type="instant_withdrawal_ng",
        amount=amount,
    )

    return result


@router.get("/deposit", response_model=Optional[ChargeDto])
async def get_deposit_charge(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: RequestChargeUseCaseDep,
    amount: Decimal = Query(...),
):
    result = await use_case.execute(
        user_id=str(context.user_id),
        charge_type="deposit_ng",
        amount=amount,
    )

    return result
