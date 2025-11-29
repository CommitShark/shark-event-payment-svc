from decimal import Decimal

from app.config import settings
from app.domain.repositories import IChargeSettingRepository
from app.domain.ports import ITicketService
from app.domain.services import ChargeCalculationService
from app.shared.errors import AppError, ErrorCodes
from app.utils.signing import sign_payload


class RequestChargeUseCase:
    def __init__(
        self,
        charge_calc_service: ChargeCalculationService,
        charge_repo: IChargeSettingRepository,
        ticket_service: ITicketService,
    ) -> None:
        self._charge_calc_service = charge_calc_service
        self._charge_repo = charge_repo
        self._ticket_service = ticket_service

    async def execute(
        self,
        user_id: str,
        charge_type: str,
        ticket_type_id: str,
    ):
        amount = await self._ticket_service.get_ticket_price(ticket_type_id)

        charge = await self._charge_repo.get_by_type(charge_type)

        charge_data = await self._charge_calc_service.get_charge_breakdown(
            charge_setting_id=charge.charge_setting_id,
            base_amount=amount,
        )

        if not charge_data:
            raise AppError(
                "Failed to generate charge data.",
                500,
                error_code=ErrorCodes.COULD_NOT_GENERATE_CHARGE,
            )

        payload = {
            **charge_data,
            "user": user_id,
            "ticket_type": ticket_type_id,
        }

        signature = sign_payload(payload, settings.charge_req_key)

        return {
            **charge_data,
            "signature": signature,
        }
