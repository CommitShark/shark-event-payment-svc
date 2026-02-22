from decimal import Decimal
from uuid import UUID, uuid4
from app.config import settings, paystack_config
from app.utils.signing import sign_payload
from app.shared.errors import AppError
from app.domain.ports import IUserService, IPaymentAdapter

from app.domain.repositories import IWalletRepository
from app.application.dto.checkout import DepositCheckoutMetaData


class CreateAttendeeDepositCheckoutUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        payment_adapter: IPaymentAdapter,
        user_service: IUserService,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._payment_adapter = payment_adapter
        self._user_service = user_service

    async def execute(
        self,
        amount: Decimal,
        user_id: UUID,
        charge_setting_id: str,
        version_id: str,
        version_number: int,
        calculated_charge: str,
        signature: str,
    ):
        reference = uuid4()
        wallet = await self._wallet_repo.get_by_user_or_create(user_id, True)

        wallet.confirm_can_deposit(amount, settings.max_attendee_wallet_balance)

        payload = {
            "amount": str(amount),
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": user_id,
        }
        expected_signature = sign_payload(payload, settings.charge_req_key)

        if expected_signature != signature:
            raise AppError("Invalid or malformed request", 400)

        metadata_payload = {
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": user_id,
            "sponsored": False,
        }

        metadata_signature = sign_payload(metadata_payload, settings.charge_req_key)

        metadata = DepositCheckoutMetaData.model_validate(
            {
                **metadata_payload,
                "signature": metadata_signature,
            }
        )

        email = await self._user_service.get_email(str(user_id))

        link = await self._payment_adapter.create_checkout_link(
            amount=amount + Decimal(calculated_charge),
            reference=str(reference),
            callback_url=paystack_config.attendee_deposit_callback,
            email=email,
            metadata=metadata.model_dump(),
        )

        return link
