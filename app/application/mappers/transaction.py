from app.domain.entities import Transaction

from ..dto.wallet import TransactionDto


def transaction_to_dto(txn: Transaction) -> TransactionDto:
    return TransactionDto(
        id=txn.id,
        reference=str(txn.reference),
        settlement_status=txn.settlement_status,
        amount=txn.amount,
        description=txn.description,
        date=txn.occurred_on,
        direction=txn.transaction_direction,
        source=txn.transaction_type,
    )
