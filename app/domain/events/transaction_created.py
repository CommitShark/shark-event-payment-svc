from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import ClassVar, TYPE_CHECKING

from .base import DomainEvent
from .registry import EventRegistry

if TYPE_CHECKING:
    from app.domain.entities import Transaction


class TransactionCreatedPayload(BaseModel):
    transaction_id: UUID
    amount: Decimal
    user_id: UUID
    resource: str
    reference: str
    resource_id: UUID
    transaction_type: str
    occurred_on: datetime

    model_config = {"frozen": True}


@EventRegistry.register
class TransactionCreatedEvent(DomainEvent[TransactionCreatedPayload]):
    _event_name: ClassVar[str] = "created"
    _group: ClassVar[str] = "transaction"

    @classmethod
    def create(cls, txn: "Transaction"):
        return cls(
            aggregate_id=str(txn.id),
            payload=TransactionCreatedPayload(
                amount=txn.amount,
                occurred_on=txn.occurred_on,
                resource=txn.resource,
                resource_id=txn.resource_id,
                transaction_id=txn.id,
                transaction_type=txn.transaction_type,
                user_id=txn.user_id,
                reference=str(txn.reference),
            ),
        )

    class Config:
        frozen = True
