from decimal import Decimal

from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError


class CreateCheckoutUseCase:
    async def execute(
        self,
        base_amount: Decimal,
        charge_setting_id: str,
        version_id: str,
        version_number: int,
        calculated_charge: str,
        user_id: str,
        event_id: str,
        ticket_type_id: str,
        signature: str,
    ):
        expected_signature = sign_payload(
            {
                "base_amount": base_amount,
                "charge_setting_id": charge_setting_id,
                "version_id": version_id,
                "version_number": version_number,
                "calculated_charge": calculated_charge,
                "user": user_id,
                "event": event_id,
                "ticket_type": ticket_type_id,
            },
            settings.charge_req_key,
        )

        if expected_signature != signature:
            raise AppError("Invalid or malformed request", 400)

        pass
