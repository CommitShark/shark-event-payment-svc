from fastapi import APIRouter
from fastapi.responses import RedirectResponse


from app.application.dto.checkout import (
    CreateCheckoutReqDto,
    CreateCheckoutResDto,
    VerifyTicketPurchaseReqDto,
    VerifyTicketPurchaseResDto,
)
from app.interfaces.fastapi.context import UserContextDep, ProtectedDep
from app.interfaces.fastapi.di import (
    CreateCheckoutUseCaseDep,
    VerifyTicketPurchaseTransactionUseCaseDep,
)

router = APIRouter(prefix="/v1/checkout", tags=["Checkout"])


@router.post(
    "/ticket-purchase",
    response_model=CreateCheckoutResDto,
    description="Generate payment link for ticket purchase",
)
async def ticket_purchase(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: CreateCheckoutUseCaseDep,
    req: CreateCheckoutReqDto,
):
    link = await use_case.execute(
        user_id=str(context.user_id),
        email=req.email,
        reservation_id=req.reservation_id,
        charge_setting_id=req.charge_setting_id,
        version_id=req.version_id,
        version_number=req.version_number,
        calculated_charge=req.calculated_charge,
        ticket_type_id=req.ticket_type_id,
        slug=req.slug,
        signature=req.signature,
    )

    return CreateCheckoutResDto(
        link=link,
    )


@router.post(
    "/verify-ticket-purchase",
    response_model=VerifyTicketPurchaseResDto,
)
async def verify_ticket_purchase(
    _: ProtectedDep,
    context: UserContextDep,
    use_case: VerifyTicketPurchaseTransactionUseCaseDep,
    req: VerifyTicketPurchaseReqDto,
):
    await use_case.execute(
        user_id=context.user_id,
        reference=req.reference,
    )

    return VerifyTicketPurchaseResDto(
        success=True,
    )
