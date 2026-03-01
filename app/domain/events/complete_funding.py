from decimal import Decimal
from pydantic import BaseModel

from .base import DomainEvent
from .registry import EventRegistry


class CompleteFundingPayload(BaseModel):
    amount_paid: Decimal
    ref: str
    date: str


@EventRegistry.register
class CompleteFundingEvent(DomainEvent[CompleteFundingPayload]):
    _group = "transaction"
    _event_name = "confirm-deposit"

    @classmethod
    def create(
        cls,
        amount_paid: Decimal,
        ref: str,
        date: str,
    ):
        return cls(
            payload=CompleteFundingPayload(
                amount_paid=amount_paid,
                ref=ref,
                date=date,
            ),
            aggregate_id=ref,
        )
