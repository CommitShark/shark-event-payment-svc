from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from app.domain.entities import Transaction

from app.domain.entities.value_objects import (
    TransactionType,
    TransactionDirection,
    TransactionSettlementStatus,
)


class TransactionListDto(BaseModel):
    id: str
    reference: str
    user_id: str
    amount: Decimal
    transaction_type: TransactionType
    transaction_direction: TransactionDirection
    settlement_status: TransactionSettlementStatus
    occurred_on: datetime

    @classmethod
    def from_domain(cls, txn: Transaction):
        return cls(
            id=str(txn.id),
            reference=str(txn.reference),
            amount=txn.amount,
            user_id=str(txn.user_id),
            transaction_type=txn.transaction_type,
            transaction_direction=txn.transaction_direction,
            settlement_status=txn.settlement_status,
            occurred_on=txn.occurred_on,
        )
