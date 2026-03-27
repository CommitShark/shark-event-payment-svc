import json
from uuid import UUID
from decimal import Decimal
from typing import Optional

from app.config import settings
from app.domain.repositories import IChargeSettingRepository
from app.domain.ports import ITicketService, IEventService
from app.domain.services import ChargeCalculationService
from app.shared.errors import AppError, ErrorCodes
from app.utils.signing import sign_payload
from app.application.dto.extra import ExtraOrderIntent


class RequestChargeUseCase:

    def __init__(
        self,
        charge_calc_service: ChargeCalculationService,
        charge_repo: IChargeSettingRepository,
        ticket_service: ITicketService,
        event_service: IEventService,
    ) -> None:
        self._charge_calc_service = charge_calc_service
        self._charge_repo = charge_repo
        self._ticket_service = ticket_service
        self._event_service = event_service

    async def execute(
        self,
        user_id: str,
        charge_type: str,
        amount: Optional[Decimal] = None,
    ):
        if charge_type == "instant_withdrawal_ng":
            return await self.instant_withdrawal_charge(user_id, amount)
        elif charge_type == "deposit_ng":
            return await self.deposit_charge(user_id, amount)

        raise AppError("Unsupported charge type requested", 400)

    async def ticket_charge(
        self,
        user_id: str,
        occurrence_id: str,
        ticket_type_id: str,
        event_id: str,
        quantity: int,
        extras: Optional[list[ExtraOrderIntent]] = None,
    ):
        """
        Calculate charges for ticket purchase including extras.
        Returns separate charge groups for tickets and extras.
        """

        ticket_base_price = await self._ticket_service.get_ticket_price(ticket_type_id)
        ticket_subtotal = ticket_base_price * Decimal(quantity)

        # Get charge setting for ticket purchases
        charge = await self._charge_repo.get_by_type("ticket_purchase_ng")

        # Calculate ticket charge
        ticket_charge_data = await self._charge_calc_service.get_charge_breakdown(
            charge_setting_id=charge.charge_setting_id,
            base_amount=ticket_base_price,
            quantity=quantity,
        )

        if not ticket_charge_data:
            raise AppError(
                "Failed to generate ticket charge data.",
                500,
                error_code=ErrorCodes.COULD_NOT_GENERATE_CHARGE,
            )

        charges_response = []

        # Add ticket charge group
        charges_response.append(
            {
                "base_amount": str(ticket_subtotal),
                "charge_setting_id": ticket_charge_data["charge_setting_id"],
                "version_id": ticket_charge_data["version_id"],
                "version_number": ticket_charge_data["version_number"],
                "calculated_charge": ticket_charge_data["calculated_charge"],
                "quantity": quantity,
                "user": user_id,
                "ticket_type": ticket_type_id,
                "event_id": event_id,
                "occurrence_id": occurrence_id,
                "charge_group": "tickets",
            }
        )

        if extras and len(extras) > 0:
            # Get charge setting for extra purchases
            extra_charge_setting = await self._charge_repo.get_by_type(
                "extra_purchase_ng"
            )

            # Calculate extras subtotal with version tracking
            extras_subtotal = Decimal(0)
            extra_details = []
            extra_price_mapping: dict[tuple[UUID, int], tuple[Decimal, str]] = {}

            for e in extras:
                # Get price from cache or fetch from service
                price_key = (e.extra_id, e.extra_version)

                if price_key not in extra_price_mapping:
                    extra = await self._event_service.get_active_extra_for_ticket(
                        extra_id=e.extra_id,
                        extra_version=e.extra_version,
                        ticket_type_id=UUID(ticket_type_id),
                    )
                    if not extra:
                        raise AppError("Extra not found", 404)

                    extra_price_mapping[(e.extra_id, e.extra_version)] = (
                        extra.price,
                        extra.name,
                    )

                extra_price, extra_name = extra_price_mapping[price_key]
                extras_subtotal += extra_price * Decimal(e.quantity)

                # Store details for payload
                extra_details.append(
                    {
                        "extra_id": str(e.extra_id),
                        "version": e.extra_version,
                        "quantity": e.quantity,
                        "price": str(extra_price),
                        "recipient_id": str(e.recipient_id) if e.recipient_id else None,
                        "name": extra_name,  # Include name for frontend display
                    }
                )

                # Calculate extras charge
            extras_charge_data = await self._charge_calc_service.get_charge_breakdown(
                charge_setting_id=extra_charge_setting.charge_setting_id,
                base_amount=extras_subtotal,
                quantity=1,
            )

            if not extras_charge_data:
                raise AppError(
                    "Failed to generate extras charge data.",
                    500,
                    error_code=ErrorCodes.COULD_NOT_GENERATE_CHARGE,
                )

            charges_response.append(
                {
                    "base_amount": extras_charge_data["base_amount"],
                    "charge_setting_id": extras_charge_data["charge_setting_id"],
                    "version_id": extras_charge_data["version_id"],
                    "version_number": extras_charge_data["version_number"],
                    "calculated_charge": extras_charge_data["calculated_charge"],
                    "user": user_id,
                    "event_id": event_id,
                    "occurrence_id": occurrence_id,
                    "charge_group": "extras",
                }
            )

        signature = sign_payload(
            charges_response,
            settings.charge_req_key,
        )

        print(f"Sign charge: {json.dumps(charges_response)}")

        return charges_response, signature

    async def instant_withdrawal_charge(
        self,
        user_id: str,
        amount: Optional[Decimal] = None,
    ):
        if not amount:
            raise AppError("Amount is required", 422)

        charge = await self._charge_repo.get_by_type("instant_withdrawal_ng")

        charge_data = await self._charge_calc_service.get_charge_breakdown(
            charge_setting_id=charge.charge_setting_id,
            base_amount=amount,
            quantity=1,
        )

        if not charge_data:
            raise AppError(
                "Failed to generate charge data.",
                500,
                error_code=ErrorCodes.COULD_NOT_GENERATE_CHARGE,
            )

        payload = {
            "base_amount": charge_data["base_amount"],
            "charge_setting_id": charge_data["charge_setting_id"],
            "version_id": charge_data["version_id"],
            "version_number": charge_data["version_number"],
            "calculated_charge": charge_data["calculated_charge"],
            "user": user_id,
        }

        signature = sign_payload(payload, settings.charge_req_key)

        if settings.disable_withdrawal_charges == 1:
            return None

        return {
            **charge_data,
            "signature": signature,
        }

    async def deposit_charge(
        self,
        user_id: str,
        amount: Optional[Decimal] = None,
    ):
        if not amount:
            raise AppError("Amount is required", 422)

        if amount < Decimal("100"):
            raise AppError("Minimum deposit amount is 100 naira", 400)

        charge = await self._charge_repo.get_by_type("deposit_ng")
        if not charge.is_active:
            raise AppError("Selected charge is inactive", 400)

        charge_data = await self._charge_calc_service.get_charge_breakdown(
            charge_setting_id=charge.charge_setting_id,
            base_amount=amount,
            quantity=1,
        )

        if not charge_data:
            raise AppError(
                "Failed to generate charge data.",
                500,
                error_code=ErrorCodes.COULD_NOT_GENERATE_CHARGE,
            )

        payload = {
            "base_amount": charge_data["base_amount"],
            "charge_setting_id": charge_data["charge_setting_id"],
            "version_id": charge_data["version_id"],
            "version_number": charge_data["version_number"],
            "calculated_charge": charge_data["calculated_charge"],
            "user": user_id,
        }

        signature = sign_payload(payload, settings.charge_req_key)

        return {
            **charge_data,
            "signature": signature,
        }
