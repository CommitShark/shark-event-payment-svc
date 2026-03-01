from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.config import settings, paystack_config
from app.utils.signing import sign_payload
from app.shared.errors import AppError
from app.domain.ports import IUserService, IPaymentAdapter, IEventBus

from app.domain.repositories import IWalletRepository, ITransactionRepository
from app.domain.entities import Transaction
from app.domain.entities.value_objects import ChargeData
from app.application.dto.checkout import DepositCheckoutMetaData


class CreateAttendeeDepositCheckoutUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        txn_repo: ITransactionRepository,
        payment_adapter: IPaymentAdapter,
        user_service: IUserService,
        event_bus: IEventBus,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._payment_adapter = payment_adapter
        self._user_service = user_service
        self._txn_repo = txn_repo
        self._event_bus = event_bus

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
            "base_amount": str(amount),
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": str(user_id),
        }
        expected_signature = sign_payload(payload, settings.charge_req_key)

        if expected_signature != signature:
            raise AppError("Invalid or malformed request", 400)

        metadata_payload = {
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": str(user_id),
            "amount": str(amount),
            "sponsored": False,
            "action": "deposit",
        }

        metadata_signature = sign_payload(metadata_payload, settings.charge_req_key)

        metadata = DepositCheckoutMetaData.model_validate(
            {
                **metadata_payload,
                "signature": metadata_signature,
            }
        )

        email = await self._user_service.get_email(str(user_id))

        txn = Transaction.create(
            amount=amount,
            charge_data=ChargeData(
                charge_setting_id=charge_setting_id,
                charge_amount=Decimal(calculated_charge),
                sponsored=False,
                version_id=version_id,
                version_number=version_number,
            ),
            occurred_on=datetime.now(timezone.utc),
            reference=reference,
            resource="deposit",
            resource_id=reference,
            source="payment_provider",
            transaction_type="wallet_funding",
            user_id=user_id,
        )

        await self._txn_repo.save(txn)

        link = await self._payment_adapter.create_checkout_link(
            amount=amount + Decimal(calculated_charge),
            reference=str(reference),
            callback_url=paystack_config.attendee_deposit_callback,
            email=email,
            metadata=metadata.model_dump(),
        )

        for e in txn.events:
            await self._event_bus.publish(e)

        return link
