import logging
from decimal import Decimal
from uuid import UUID

from app.domain.ports import IPaymentAdapter, IEventBus
from app.domain.repositories import ITransactionRepository
from app.domain.entities import Transaction
from app.domain.entities.value_objects import ChargeData
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError


logger = logging.getLogger(__name__)


class VerifyTicketPurchaseTransactionUseCase:
    def __init__(
        self,
        payment_adapter: IPaymentAdapter,
        txn_repo: ITransactionRepository,
        event_bus: IEventBus,
    ) -> None:
        self._payment_adapter = payment_adapter
        self._txn_repo = txn_repo
        self._event_bus = event_bus

    async def execute(self, reference: str, user_id: UUID):
        # Check if transaction reference has already been recorded
        existing_txn = await self._txn_repo.get_by_reference_or_none(UUID(reference))

        if existing_txn:
            logger.debug(
                "transaction for reference %s already exists",
                reference,
            )
            return

        ext_transaction = await self._payment_adapter.get_valid_transaction(reference)

        if not ext_transaction.metadata:
            logger.debug("Metadata not found")
            raise AppError("Malformed transaction. Please contact support", 500)

        metadata: dict = ext_transaction.metadata
        signature = metadata.pop("signature", None)

        if "referrer" in metadata:
            _ = metadata.pop("referrer")

        if not signature:
            logger.debug("Signature not found")
            raise AppError("Malformed transaction. Please contact support", 500)

        expected_signature = sign_payload(metadata, settings.charge_req_key)

        if expected_signature != signature:
            logger.debug("Signature mismatch")
            raise AppError("Malformed transaction. Please contact support", 500)

        txn = Transaction.create(
            amount=ext_transaction.amount,
            charge_data=ChargeData(
                charge_setting_id=metadata.pop("charge_setting_id"),
                charge_amount=Decimal(metadata.pop("calculated_charge")),
                sponsored=bool(metadata.pop("sponsored")),
                version_id=metadata.pop("version_id"),
                version_number=metadata.pop("version_number"),
            ),
            occurred_on=ext_transaction.occurred_on,
            reference=ext_transaction.reference,
            resource="ticket",
            resource_id=UUID(metadata.pop("ticket_type_id")),
            source="payment_provider",
            transaction_type="purchase",
            user_id=UUID(metadata.pop("user")),
            metadata=metadata,
        )

        if user_id != txn.user_id:
            logger.debug(
                f"User mismatch. \nOriginal User = {txn.user_id} \nUser Attempting Validation = {user_id}"
            )
            raise AppError("Cannot validate transaction initiated by another user", 403)

        await self._txn_repo.save(txn)

        for e in txn.events:
            await self._event_bus.publish(e)
