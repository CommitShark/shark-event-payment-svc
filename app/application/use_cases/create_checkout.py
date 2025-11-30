from decimal import Decimal
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError
from app.domain.ports import ITicketService, IPaymentAdapter

from app.application.dto.checkout import CheckoutMetaData
from app.config import paystack_config


class CreateCheckoutUseCase:
    def __init__(
        self, ticket_service: ITicketService, payment_adapter: IPaymentAdapter
    ) -> None:
        self._ticket_service = ticket_service
        self._payment_adapter = payment_adapter

    async def execute(
        self,
        reservation_id: str,
        charge_setting_id: str,
        version_id: str,
        version_number: int,
        calculated_charge: str,
        user_id: str,
        ticket_type_id: str,
        slug: str,
        email: str,
        signature: str,
    ):
        is_valid, error = await self._ticket_service.reservation_is_valid(
            reservation_id
        )

        if not is_valid:
            raise AppError(error or "Invalid or expired reservation", 400)

        base_amount = await self._ticket_service.get_ticket_price(ticket_type_id)

        payload = {
            "base_amount": str(base_amount),
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": user_id,
            "ticket_type": ticket_type_id,
            "slug": slug,
        }
        expected_signature = sign_payload(payload, settings.charge_req_key)

        if expected_signature != signature:
            raise AppError("Invalid or malformed request", 400)

        metadata_payload = {
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "ticket_type_id": ticket_type_id,
            "slug": slug,
            "user": user_id,
            "sponsored": False,
        }

        print(f"Checkout metadata \n{metadata_payload}")
        metadata_signature = sign_payload(metadata_payload, settings.charge_req_key)

        metadata = CheckoutMetaData.model_validate(
            {
                **metadata_payload,
                "signature": metadata_signature,
            }
        )

        link = await self._payment_adapter.create_checkout_link(
            amount=base_amount + Decimal(calculated_charge),
            reference=reservation_id,
            callback_url=paystack_config.ticket_purchase_callback.format(
                slug=slug,
                purchase=ticket_type_id,
                reservation=reservation_id,
            ),
            email=email,
            metadata=metadata.model_dump(),
        )

        return link
