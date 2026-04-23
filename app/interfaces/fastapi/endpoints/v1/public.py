from fastapi import APIRouter
from app.application.dto.checkout import (
    PublicCreateCheckoutReqDto,
    CreateCheckoutResDto,
    VerifyTicketPurchaseReqDto,
    VerifyTicketPurchaseResDto,
    VerifyTicketPurchaseGateResDto,
    GateCreateCheckoutReqDto,
    GateCreateCheckoutResDto,
)
from app.application.dto.charge_request import (
    GetChargeResDto,
    ChargeDto,
    PublicGetChargeReqDto,
)

from app.interfaces.fastapi.di import (
    CreateCheckoutUseCaseDep,
    VerifyTicketPurchaseTransactionUseCaseDep,
    RequestChargeUseCaseDep,
)
from app.config import settings

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
        req=req,
        user_id=req.user_auth_id,
    )

    return CreateCheckoutResDto(
        link=link,
    )


@router.post(
    "/checkout/ticket-purchase/gate",
    response_model=GateCreateCheckoutResDto,
    description="Generate payment link for ticket purchase at the gate",
)
async def ticket_purchase_gate(
    use_case: CreateCheckoutUseCaseDep,
    req: GateCreateCheckoutReqDto,
):
    return await use_case.at_gate(
        req=req,
    )


@router.post(
    "/checkout/verify-ticket-purchase",
    response_model=VerifyTicketPurchaseResDto,
)
async def verify_ticket_purchase(
    use_case: VerifyTicketPurchaseTransactionUseCaseDep,
    req: VerifyTicketPurchaseReqDto,
):
    amount, _ = await use_case.execute(
        reference=req.reference,
        validate_only=not settings.debug,
    )

    return VerifyTicketPurchaseResDto(
        success=True,
        amount=amount,
    )


@router.post(
    "/checkout/verify-ticket-purchase/gate",
    response_model=VerifyTicketPurchaseGateResDto,
)
async def verify_ticket_purchase_gate(
    use_case: VerifyTicketPurchaseTransactionUseCaseDep,
    req: VerifyTicketPurchaseReqDto,
):
    amount, qr = await use_case.validate_gate(req.reference)

    return VerifyTicketPurchaseGateResDto(
        success=True,
        amount=amount,
        qr=qr,
    )


@router.post(
    "/charges/ticket-purchase",
    response_model=GetChargeResDto,
)
async def get_ticket_type_charge(
    use_case: RequestChargeUseCaseDep,
    req: PublicGetChargeReqDto,
):
    charges, sig = await use_case.ticket_charge(
        user_id=str(req.user_id),
        ticket_type_id=str(req.ticket_type_id),
        quantity=req.quantity,
        extras=req.extras,
        occurrence_id=req.occurrence_id,
        event_id=req.event_id,
        pay_more_amount=req.pay_more_amount,
    )

    return GetChargeResDto(
        charges=[ChargeDto.model_validate(c) for c in charges],
        signature=sig,
    )
