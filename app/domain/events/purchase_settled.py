from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import ClassVar, TYPE_CHECKING, Any
from app.shared.errors import AppError

from .base import DomainEvent

if TYPE_CHECKING:
    from app.domain.entities.transaction import Transaction


class PurchaseSettledPayload(BaseModel):
    amount: Decimal
    user_id: UUID
    resource: str
    reference: str
    resource_id: UUID
    slug: str
    settlement_data: list[Any]  # TODO: Resolve circular Deps

    model_config = {"frozen": True}


class PurchaseSettledEvent(DomainEvent[PurchaseSettledPayload]):
    _event_name: ClassVar[str] = "purchased"
    _group: ClassVar[str] = "transaction"

    @classmethod
    def create(cls, txn: "Transaction"):
        slug = txn.metadata.get("slug", None) if txn.metadata else None

        if not slug:
            raise AppError("Malformed transaction. Slug not found", 400)

        return cls(
            aggregate_id=str(txn.reference),
            payload=PurchaseSettledPayload(
                amount=txn.amount,
                resource=txn.resource,
                resource_id=txn.resource_id,
                user_id=txn.user_id,
                reference=str(txn.reference),
                slug=slug,
                settlement_data=txn.settlement_data,
            ),
        )

    class Config:
        frozen = True
