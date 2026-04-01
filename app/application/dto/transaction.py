from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

from app.domain.entities import Transaction

from app.domain.entities.value_objects import (
    TransactionType,
    TransactionDirection,
    TransactionSettlementStatus,
    TransactionSource,
)


class UpdateTransactionStatusReqDto(BaseModel):
    status: TransactionSettlementStatus
    reason: str


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


class TransactionDetailsDto(BaseModel):
    id: str
    reference: str
    user_id: str
    amount: Decimal

    transaction_type: TransactionType
    transaction_direction: TransactionDirection
    settlement_status: TransactionSettlementStatus

    resource: str
    resource_id: str
    source: TransactionSource

    description: str

    occurred_on: datetime
    created_at: datetime
    delayed_settlement_until: Optional[datetime] = None

    charge_total: Decimal
    is_charge_sponsored: bool

    metadata: Optional[dict] = None
    parent_id: Optional[str] = None

    @classmethod
    def from_domain(cls, txn: Transaction):
        return cls(
            id=str(txn.id),
            reference=str(txn.reference),
            user_id=str(txn.user_id),
            amount=txn.amount,
            transaction_type=txn.transaction_type,
            transaction_direction=txn.transaction_direction,
            settlement_status=txn.settlement_status,
            resource=txn.resource,
            resource_id=str(txn.resource_id),
            source=txn.source,
            description=txn.description,
            occurred_on=txn.occurred_on,
            created_at=txn.created_at,
            delayed_settlement_until=txn.delayed_settlement_until,
            charge_total=txn.get_total_charge_amount(),
            is_charge_sponsored=txn.is_charge_sponsored(),
            metadata=txn.metadata,
            parent_id=str(txn.parent_id) if txn.parent_id else None,
        )
