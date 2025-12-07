from fastapi import APIRouter, Query
from decimal import Decimal
from app.application.dto.charge_request import GetChargeResDto

from app.interfaces.fastapi.context import UserContextDep, ProtectedDep
from app.interfaces.fastapi.di import RequestChargeUseCaseDep

router = APIRouter(prefix="/v1/charges", tags=["Charges"])


@router.get("/ticket-purchase", response_model=GetChargeResDto)
async def get_ticket_type_charge(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: RequestChargeUseCaseDep,
    ticket_type_id: str = Query(...),
    slug: str = Query(...),
):
    result = await use_case.execute(
        user_id=str(context.user_id),
        charge_type="ticket_purchase_ng",
        ticket_type_id=ticket_type_id,
        slug=slug,
    )

    return result


@router.get("/instant-withdrawal", response_model=GetChargeResDto)
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
