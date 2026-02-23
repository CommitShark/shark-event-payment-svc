from fastapi import APIRouter, Query
from app.application.dto.checkout import (
    PublicCreateCheckoutReqDto,
    CreateCheckoutResDto,
    VerifyTicketPurchaseReqDto,
    VerifyTicketPurchaseResDto,
)
from app.application.dto.charge_request import GetChargeResDto

from app.interfaces.fastapi.di import (
    CreateCheckoutUseCaseDep,
    VerifyTicketPurchaseTransactionUseCaseDep,
    RequestChargeUseCaseDep,
)

router = APIRouter(prefix="/v1/public", tags=["Public"])


@router.post(
    "/checkout/ticket-purchase",
    response_model=CreateCheckoutResDto,
    description="Generate payment link for ticket purchase",
)
async def ticket_purchase(
    use_case: CreateCheckoutUseCaseDep,
    req: PublicCreateCheckoutReqDto,
):
    link = await use_case.execute(
        user_id=req.user_auth_id,
        email=req.email,
        reservation_id=req.reservation_id,
        charge_setting_id=req.charge_setting_id,
        version_id=req.version_id,
        version_number=req.version_number,
        calculated_charge=req.calculated_charge,
        ticket_type_id=req.ticket_type_id,
        slug=req.slug,
        signature=req.signature,
        quantity=req.quantity,
    )

    return CreateCheckoutResDto(
        link=link,
    )


@router.post(
    "/checkout/verify-ticket-purchase",
    response_model=VerifyTicketPurchaseResDto,
)
async def verify_ticket_purchase(
    use_case: VerifyTicketPurchaseTransactionUseCaseDep,
    req: VerifyTicketPurchaseReqDto,
):
    await use_case.execute(
        reference=req.reference,
    )

    return VerifyTicketPurchaseResDto(
        success=True,
    )


@router.get(
    "/charges/ticket-purchase",
    response_model=GetChargeResDto,
)
async def get_ticket_type_charge(
    use_case: RequestChargeUseCaseDep,
    ticket_type_id: str = Query(...),
    quantity: int = Query(...),
    slug: str = Query(...),
    user_id: str = Query(...),
):
    result = await use_case.execute(
        user_id=user_id,
        charge_type="ticket_purchase_ng",
        ticket_type_id=ticket_type_id,
        slug=slug,
        quantity=quantity,
    )

    return result
