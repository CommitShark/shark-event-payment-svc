from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import ClassVar, TYPE_CHECKING

from .base import DomainEvent
from .registry import EventRegistry

if TYPE_CHECKING:
    from app.domain.entities import Transaction


class PurchaseSettledPayload(BaseModel):
    amount: Decimal
    user_id: UUID
    resource: str
    reference: str
    resource_id: UUID

    model_config = {"frozen": True}


class PurchaseSettledEvent(DomainEvent[PurchaseSettledPayload]):
    _event_name: ClassVar[str] = "purchased"
    _group: ClassVar[str] = "transaction"

    @classmethod
    def create(cls, txn: "Transaction"):
        return cls(
            aggregate_id=str(txn.id),
            payload=PurchaseSettledPayload(
                amount=txn.amount,
                resource=txn.resource,
                resource_id=txn.resource_id,
                user_id=txn.user_id,
                reference=str(txn.reference),
            ),
        )

    class Config:
        frozen = True
