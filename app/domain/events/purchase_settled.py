from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import ClassVar, TYPE_CHECKING, Any
from app.shared.errors import AppError
from app.domain.dto.event import EventOccurrence

from .base import DomainEvent

if TYPE_CHECKING:
    from app.domain.entities.transaction import Transaction


class PurchaseSettledPayload(BaseModel):
    amount: Decimal
    user_id: UUID
    resource: str
    reference: str
    resource_id: UUID
    event_id: str
    occurrence_id: str
    settlement_data: list[Any]  # TODO: Resolve circular Deps

    model_config = {"frozen": True}


class PurchaseSettledEvent(DomainEvent[PurchaseSettledPayload]):
    _event_name: ClassVar[str] = "purchased"
    _group: ClassVar[str] = "transaction"

    @classmethod
    def create(cls, txn: "Transaction"):
        event = txn.metadata.get("event", None) if txn.metadata else None

        if not event:
            raise AppError("Malformed transaction. Event not found in metadata", 400)

        parsed = EventOccurrence.model_validate(event)

        return cls(
            aggregate_id=str(txn.reference),
            payload=PurchaseSettledPayload(
                amount=txn.amount,
                resource=txn.resource,
                resource_id=txn.resource_id,
                user_id=txn.user_id,
                reference=str(txn.reference),
                event_id=parsed.id,
                occurrence_id=parsed.occurrence,
                settlement_data=txn.settlement_data,
            ),
        )

    class Config:
        frozen = True
