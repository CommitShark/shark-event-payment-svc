from app.domain.entities import Transaction, Wallet

from ..dto.wallet import TransactionDto, BalanceDto


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


def wallet_to_dto(w: Wallet) -> BalanceDto:
    return BalanceDto(
        available=w.balance,
        bank_details=w.bank_details,
        has_pin=w.has_pin,
        pending=w.pending_balance,
    )
