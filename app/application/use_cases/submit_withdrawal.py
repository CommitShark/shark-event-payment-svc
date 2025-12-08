from datetime import datetime, timezone
from uuid import uuid4, UUID
from decimal import Decimal
from app.domain.repositories import IWalletRepository, ITransactionRepository
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError
from app.domain.entities import Transaction
from app.domain.entities.value_objects import ChargeData
from app.domain.ports import IEventBus


class SubmitWithdrawalUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        txn_repo: ITransactionRepository,
        event_bus: IEventBus,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._txn_repo = txn_repo
        self._event_bus = event_bus

    async def execute(
        self,
        charge_setting_id: str,
        version_id: str,
        version_number: int,
        calculated_charge: str,
        user_id: str,
        amount: Decimal,
        signature: str,
    ):
        wallet = await self._wallet_repo.get_by_user_or_create(
            UUID(user_id),
            lock_for_update=True,
        )

        if not wallet.can_withdraw(Decimal(amount) + Decimal(calculated_charge)):
            raise AppError("Insufficient balance", 400)

        payload = {
            "base_amount": str(amount),
            "charge_setting_id": charge_setting_id,
            "version_id": version_id,
            "version_number": version_number,
            "calculated_charge": calculated_charge,
            "user": user_id,
        }

        expected_signature = sign_payload(payload, settings.charge_req_key)

        if expected_signature != signature:
            raise AppError("Invalid or malformed request", 400)

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
            reference=uuid4(),
            resource="withdrawal",
            resource_id=uuid4(),
            source="wallet",
            transaction_type="withdrawal",
            metadata=None,
            user_id=UUID(user_id),
        )

        wallet.withdraw(Decimal(amount) + Decimal(calculated_charge))

        await self._txn_repo.save(txn)
        await self._wallet_repo.save(wallet)

        for e in txn.events:
            await self._event_bus.publish(e)
