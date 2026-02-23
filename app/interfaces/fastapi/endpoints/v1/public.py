from fastapi import APIRouter
from uuid import UUID
from app.application.dto.checkout import (
    PublicCreateCheckoutReqDto,
    CreateCheckoutResDto,
    PublicVerifyTicketPurchaseReqDto,
    VerifyTicketPurchaseResDto,
)

from app.interfaces.fastapi.di import (
    CreateCheckoutUseCaseDep,
    VerifyTicketPurchaseTransactionUseCaseDep,
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
    "/verify-ticket-purchase",
    response_model=VerifyTicketPurchaseResDto,
)
async def verify_ticket_purchase(
    use_case: VerifyTicketPurchaseTransactionUseCaseDep,
    req: PublicVerifyTicketPurchaseReqDto,
):
    await use_case.execute(
        user_id=UUID(req.user_auth_id),
        reference=req.reference,
    )

    return VerifyTicketPurchaseResDto(
        success=True,
    )
