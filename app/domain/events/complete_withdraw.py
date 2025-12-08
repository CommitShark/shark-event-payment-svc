from decimal import Decimal
from pydantic import BaseModel

from .base import DomainEvent
from .registry import EventRegistry


class CompleteWithdrawPayload(BaseModel):
    amount: Decimal
    ref: str
    date: str
    dest: str


@EventRegistry.register
class CompleteWithdrawEvent(DomainEvent[CompleteWithdrawPayload]):
    _group = "transaction"
    _event_name = "withdraw_successful"

    @classmethod
    def create(
        cls,
        amount: Decimal,
        ref: str,
        date: str,
        dest: str,
    ):
        return cls(
            payload=CompleteWithdrawPayload(
                amount=amount, ref=ref, date=date, dest=dest
            ),
            aggregate_id=ref,
        )
