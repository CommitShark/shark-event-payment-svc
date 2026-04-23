import json
from uuid import uuid4
from decimal import Decimal
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError, ErrorCodes
from app.domain.ports import ITicketService, IPaymentAdapter

from app.application.dto.checkout import (
    CheckoutMetaData,
    CreateCheckoutReqDto,
    GateCreateCheckoutReqDto,
    GateCreateCheckoutResDto,
)
from app.application.dto.charge_request import ChargeDto
from app.config import paystack_config


class CreateCheckoutUseCase:
    def __init__(
        self,
        ticket_service: ITicketService,
        payment_adapter: IPaymentAdapter,
    ) -> None:
        self._ticket_service = ticket_service
        self._payment_adapter = payment_adapter

    async def _create_link(
        self,
        charges: list[ChargeDto],
        user_id: str,
        ticket_type_id: str,
        quantity: int,
        event_id: str,
        occurrence_id: str,
        signature: str,
        is_gate_purchase: bool,
        slug: str,
        email: str,
        reference: str,
    ) -> str:
        ticket_charge = next((c for c in charges if c.charge_group == "tickets"), None)

        if not ticket_charge:
            raise AppError("Charge group tickets not found in payload", 422)

        extras_charge = next((c for c in charges if c.charge_group == "extras"), None)

        charges_data = []

        ticket_charge_payload = {
            "base_amount": str(ticket_charge.base_amount),
            "charge_setting_id": ticket_charge.charge_setting_id,
            "version_id": ticket_charge.version_id,
            "version_number": ticket_charge.version_number,
            "calculated_charge": ticket_charge.calculated_charge,
            "user": user_id,
            "ticket_type": ticket_type_id,
            "quantity": quantity,
            "event_id": event_id,
            "occurrence_id": occurrence_id,
            "pay_more_amount": (
                str(ticket_charge.pay_more_amount)
                if ticket_charge.pay_more_amount
                else None
            ),
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
                "event_id": event_id,
                "occurrence_id": occurrence_id,
                "charge_group": "extras",
                "pay_more_amount": None,
            }
            charges_data.append(charges_data_payload)

        expected_signature = sign_payload(charges_data, settings.charge_req_key)

        print(f"expected = {expected_signature} sig = {signature}")

        if expected_signature != signature:
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
                    "ticket_type_id": ticket_type_id,
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
                "action": "ticket_purchase",
                "is_gate_purchase": is_gate_purchase,
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

        callback = (
            paystack_config.ticket_purchase_callback.format(
                slug=slug,
                reference=reference,
                ticket=ticket_type_id,
                event=event_id,
                occurrence=occurrence_id,
            )
            if not is_gate_purchase
            else paystack_config.gate_ticket_purchase_callback.format(
                slug=slug,
                reference=reference,
                ticket=ticket_type_id,
                event=event_id,
                occurrence=occurrence_id,
            )
        )

        print(f"callback = {callback}")

        try:
            link = await self._payment_adapter.create_checkout_link(
                amount=base_amount + calculated_charge,
                reference=reference,
                callback_url=callback,
                email=email,
                metadata=metadata.model_dump(),
            )
        except AppError as e:
            if e.error_code == ErrorCodes.DUPLICATE_REFERENCE:
                await self._ticket_service.cancel_reservation(reference)

                raise AppError(
                    message="Duplicate transaction detected. Please try again.",
                    status_code=400,
                    error_code=ErrorCodes.DUPLICATE_REFERENCE,
                ) from e

            raise

        return link

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

        return await self._create_link(
            charges=req.charge.charges,
            email=req.email,
            event_id=req.event_id,
            is_gate_purchase=False,
            occurrence_id=req.occurrence_id,
            quantity=req.quantity,
            signature=req.charge.signature,
            slug=req.slug,
            ticket_type_id=req.ticket_type_id,
            user_id=user_id,
            reference=req.reservation_id,
        )

        # ticket_charge = next(
        #     (c for c in req.charge.charges if c.charge_group == "tickets"), None
        # )

        # if not ticket_charge:
        #     raise AppError("Charge group tickets not found in payload", 422)

        # extras_charge = next(
        #     (c for c in req.charge.charges if c.charge_group == "extras"), None
        # )

        # charges_data = []

        # ticket_charge_payload = {
        #     "base_amount": str(ticket_charge.base_amount),
        #     "charge_setting_id": ticket_charge.charge_setting_id,
        #     "version_id": ticket_charge.version_id,
        #     "version_number": ticket_charge.version_number,
        #     "calculated_charge": ticket_charge.calculated_charge,
        #     "user": user_id,
        #     "ticket_type": req.ticket_type_id,
        #     "quantity": req.quantity,
        #     "event_id": req.event_id,
        #     "occurrence_id": req.occurrence_id,
        #     "charge_group": "tickets",
        # }

        # charges_data.append(ticket_charge_payload)

        # charges_data_payload = None
        # if extras_charge is not None:
        #     charges_data_payload = {
        #         "base_amount": str(extras_charge.base_amount),
        #         "charge_setting_id": extras_charge.charge_setting_id,
        #         "version_id": extras_charge.version_id,
        #         "version_number": extras_charge.version_number,
        #         "calculated_charge": extras_charge.calculated_charge,
        #         "user": user_id,
        #         "event_id": req.event_id,
        #         "occurrence_id": req.occurrence_id,
        #         "charge_group": "extras",
        #     }
        #     charges_data.append(charges_data_payload)

        # expected_signature = sign_payload(charges_data, settings.charge_req_key)

        # print(f"expected = {expected_signature} sig = {req.charge.signature}")

        # if expected_signature != req.charge.signature:
        #     print(f"Signed payload {json.dumps(charges_data)}")
        #     raise AppError("Invalid or malformed request", 400)

        # metadata_payload = [
        #     ticket_charge_payload,
        # ]

        # if charges_data_payload:
        #     metadata_payload.append(charges_data_payload)

        # metadata_signature = sign_payload(metadata_payload, settings.charge_req_key)

        # metadata = CheckoutMetaData.model_validate(
        #     {
        #         "ticket_charge": {
        #             **ticket_charge_payload,
        #             "ticket_type_id": req.ticket_type_id,
        #             "sponsored": False,
        #         },
        #         "extras_charge": (
        #             {
        #                 **charges_data_payload,
        #                 "sponsored": False,
        #             }
        #             if charges_data_payload
        #             else None
        #         ),
        #         "signature": metadata_signature,
        #         "action": "ticket_purchase",
        #     }
        # )

        # base_amount = ticket_charge.base_amount + (
        #     extras_charge.base_amount if extras_charge else Decimal(0)
        # )

        # calculated_charge = (
        #     Decimal(ticket_charge.calculated_charge)
        #     if ticket_charge.calculated_charge
        #     else Decimal(0)
        # ) + (
        #     Decimal(extras_charge.calculated_charge)
        #     if extras_charge and extras_charge.calculated_charge
        #     else Decimal(0)
        # )

        # try:
        #     link = await self._payment_adapter.create_checkout_link(
        #         amount=base_amount + calculated_charge,
        #         reference=req.reservation_id,
        #         callback_url=paystack_config.ticket_purchase_callback.format(
        #             slug=req.slug,
        #             reservation=req.reservation_id,
        #         ),
        #         email=req.email,
        #         metadata=metadata.model_dump(),
        #     )
        # except AppError as e:
        #     if e.error_code == ErrorCodes.DUPLICATE_REFERENCE:
        #         await self._ticket_service.cancel_reservation(req.reservation_id)

        #         raise AppError(
        #             message="Duplicate transaction detected. Please try again.",
        #             status_code=400,
        #             error_code=ErrorCodes.DUPLICATE_REFERENCE,
        #         ) from e

        #     raise

        # return link

    async def at_gate(self, req: GateCreateCheckoutReqDto):
        ticket_charge = next(
            (c for c in req.charge.charges if c.charge_group == "tickets"), None
        )

        if not ticket_charge:
            raise AppError("Charge group tickets not found in payload", 422)

        reference = str(uuid4())

        link = await self._create_link(
            charges=req.charge.charges,
            email=req.email,
            user_id=req.user_auth_id,
            event_id=req.event_id,
            is_gate_purchase=True,
            occurrence_id=req.occurrence_id,
            quantity=1,
            signature=req.charge.signature,
            slug=req.slug,
            ticket_type_id=req.ticket_type_id,
            reference=reference,
        )

        return GateCreateCheckoutResDto(
            link=link,
            reference=reference,
        )
