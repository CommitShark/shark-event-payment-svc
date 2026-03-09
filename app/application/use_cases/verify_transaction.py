import logging
import json
from decimal import Decimal
from uuid import UUID

from app.domain.ports import IPaymentAdapter, IEventBus
from app.domain.repositories import ITransactionRepository
from app.domain.entities import Transaction
from app.application.dto.checkout import CheckoutMetaData
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

    async def execute(self, reference: str, user_id: UUID | None = None):
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

        metadata = CheckoutMetaData.model_validate(ext_transaction.metadata)

        ticket_charge_payload = metadata.ticket_charge.model_dump()
        if "sponsored" in ticket_charge_payload:
            _ = ticket_charge_payload.pop("sponsored")

        ticket_type_id = ticket_charge_payload.pop("ticket_type_id")

        charges_data = [
            {
                **ticket_charge_payload,
                "charge_group": "tickets",
                "ticket_type": ticket_type_id,
            }
        ]

        if metadata.extras_charge:
            extra_charge_payload = metadata.extras_charge.model_dump()
            if "sponsored" in extra_charge_payload:
                _ = extra_charge_payload.pop("sponsored")
            charges_data.append({**extra_charge_payload, "charge_group": "extras"})

        expected_signature = sign_payload(charges_data, settings.charge_req_key)

        if expected_signature != metadata.signature:
            print("Signature mismatch")
            raise AppError("Malformed transaction. Please contact support", 500)

        charge_data: list[ChargeData] = [
            ChargeData(
                charge_setting_id=metadata.ticket_charge.charge_setting_id,
                charge_amount=Decimal(metadata.ticket_charge.calculated_charge),
                sponsored=bool(metadata.ticket_charge.sponsored),
                version_id=metadata.ticket_charge.version_id,
                version_number=metadata.ticket_charge.version_number,
                charge_group="tickets",
            )
        ]

        if metadata.extras_charge:
            charge_data.append(
                ChargeData(
                    charge_setting_id=metadata.extras_charge.charge_setting_id,
                    charge_amount=Decimal(metadata.extras_charge.calculated_charge),
                    sponsored=bool(metadata.extras_charge.sponsored),
                    version_id=metadata.extras_charge.version_id,
                    version_number=metadata.extras_charge.version_number,
                    charge_group="extras",
                )
            )

        txn = Transaction.create(
            amount=ext_transaction.amount,
            charge_data=charge_data,
            occurred_on=ext_transaction.occurred_on,
            reference=ext_transaction.reference,
            resource="ticket",
            resource_id=UUID(metadata.ticket_charge.ticket_type_id),
            source="payment_provider",
            transaction_type="purchase",
            user_id=UUID(metadata.ticket_charge.user),
            metadata={
                "slug": metadata.ticket_charge.slug,
            },
        )

        if user_id and user_id != txn.user_id:
            logger.debug(
                f"User mismatch. \nOriginal User = {txn.user_id} \nUser Attempting Validation = {user_id}"
            )
            raise AppError("Cannot validate transaction initiated by another user", 403)

        await self._txn_repo.save(txn)

        for e in txn.events:
            await self._event_bus.publish(e)
