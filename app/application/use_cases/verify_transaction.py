from decimal import Decimal
from uuid import UUID

from app.domain.ports import IPaymentAdapter
from app.domain.repositories import ITransactionRepository
from app.domain.entities import Transaction, ChargeData
from app.config import settings
from app.utils.signing import sign_payload
from app.shared.errors import AppError


class VerifyTicketPurchaseTransactionUseCase:
    def __init__(
        self,
        payment_adapter: IPaymentAdapter,
        txn_repo: ITransactionRepository,
    ) -> None:
        self._payment_adapter = payment_adapter
        self._txn_repo = txn_repo

    async def execute(self, reference: str, user_id: UUID):
        ext_transaction = await self._payment_adapter.get_valid_transaction(reference)

        if not ext_transaction.metadata:
            print("Metadata not found")
            raise AppError("Malformed transaction. Please contact support", 500)

        metadata: dict = ext_transaction.metadata
        signature = metadata.pop("signature", None)
        _ = metadata.pop("referrer")

        if not signature:
            print("Signature not found")
            raise AppError("Malformed transaction. Please contact support", 500)

        print(f"Loaded metadata \n{metadata}")
        expected_signature = sign_payload(metadata, settings.charge_req_key)

        if expected_signature != signature:
            print("Signature mismatch")
            raise AppError("Malformed transaction. Please contact support", 500)

        txn = Transaction.create(
            amount=ext_transaction.amount,
            charge_data=ChargeData(
                charge_setting_id=metadata["charge_setting_id"],
                charge_amount=Decimal(metadata["calculated_charge"]),
                sponsored=bool(metadata["sponsored"]),
                version_id=metadata["version_id"],
                version_number=metadata["version_number"],
            ),
            occurred_on=ext_transaction.occurred_on,
            reference=ext_transaction.reference,
            resource="ticket",
            resource_id=UUID(metadata["ticket_type_id"]),
            source="payment_provider",
            transaction_type="purchase",
            user_id=UUID(metadata["user"]),
        )

        if user_id != txn.user_id:
            print(
                f"User mismatch. \nOriginal User = {txn.user_id} \nUser Attempting Validation = {user_id}"
            )
            raise AppError("Cannot validate transaction initiated by another user", 403)

        self._txn_repo.save(txn)
        print(f"Created Transaction: \n{txn.model_dump_json()}")

        # TODO: Close reservation
