import json
from decimal import Decimal
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError
from app.domain.ports import ITicketService, IPaymentAdapter

from app.application.dto.checkout import CheckoutMetaData, CreateCheckoutReqDto
from app.config import paystack_config


class CreateCheckoutUseCase:
    def __init__(
        self,
        ticket_service: ITicketService,
        payment_adapter: IPaymentAdapter,
    ) -> None:
        self._ticket_service = ticket_service
        self._payment_adapter = payment_adapter

    async def execute(
        self,
        req: CreateCheckoutReqDto,
        user_id: str,
    ):
        is_valid, error = await self._ticket_service.reservation_is_valid(
            req.reservation_id
        )

        if not is_valid:
            raise AppError(error or "Invalid or expired reservation", 400)

        ticket_charge = next(
            (c for c in req.charge.charges if c.charge_group == "tickets"), None
        )

        if not ticket_charge:
            raise AppError("Charge group tickets not found in payload", 422)

        extras_charge = next(
            (c for c in req.charge.charges if c.charge_group == "extras"), None
        )

        charges_data = []

        ticket_charge_payload = {
            "base_amount": str(ticket_charge.base_amount),
            "charge_setting_id": ticket_charge.charge_setting_id,
            "version_id": ticket_charge.version_id,
            "version_number": ticket_charge.version_number,
            "calculated_charge": ticket_charge.calculated_charge,
            "user": user_id,
            "ticket_type": req.ticket_type_id,
            "slug": req.slug,
            "quantity": req.quantity,
            "charge_group": "tickets",
        }

        charges_data.append(ticket_charge_payload)

        charges_data_payload = None
        if extras_charge is not None:
            charges_data_payload = {
                "base_amount": str(extras_charge.base_amount),
                "charge_setting_id": extras_charge.charge_setting_id,
                "version_id": extras_charge.version_id,
                "version_number": extras_charge.version_number,
                "calculated_charge": extras_charge.calculated_charge,
                "user": user_id,
                "charge_group": "extras",
            }
            charges_data.append(charges_data_payload)

        expected_signature = sign_payload(charges_data, settings.charge_req_key)

        print(f"expected = {expected_signature} sig = {req.charge.signature}")

        if expected_signature != req.charge.signature:
            print(f"Signed payload {json.dumps(charges_data)}")
            raise AppError("Invalid or malformed request", 400)

        metadata_payload = [
            ticket_charge_payload,
        ]

        if charges_data_payload:
            metadata_payload.append(charges_data_payload)

        metadata_signature = sign_payload(metadata_payload, settings.charge_req_key)

        metadata = CheckoutMetaData.model_validate(
            {
                "ticket_charge": {
                    **ticket_charge_payload,
                    "ticket_type_id": req.ticket_type_id,
                    "sponsored": False,
                },
                "extras_charge": (
                    {
                        **charges_data_payload,
                        "sponsored": False,
                    }
                    if charges_data_payload
                    else None
                ),
                "signature": metadata_signature,
            }
        )

        base_amount = ticket_charge.base_amount + (
            extras_charge.base_amount if extras_charge else Decimal(0)
        )

        calculated_charge = (
            Decimal(ticket_charge.calculated_charge)
            if ticket_charge.calculated_charge
            else Decimal(0)
        ) + (
            Decimal(extras_charge.calculated_charge)
            if extras_charge and extras_charge.calculated_charge
            else Decimal(0)
        )

        link = await self._payment_adapter.create_checkout_link(
            amount=base_amount + calculated_charge,
            reference=req.reservation_id,
            callback_url=paystack_config.ticket_purchase_callback.format(
                slug=req.slug,
                reservation=req.reservation_id,
            ),
            email=req.email,
            metadata=metadata.model_dump(),
        )

        return link
