from pydantic import BaseModel
from decimal import Decimal
from typing import ClassVar, TYPE_CHECKING

from .base import DomainEvent

if TYPE_CHECKING:
    from app.domain.entities import Transaction


class WalletFundedPayload(BaseModel):
    amount: Decimal
    user_id: str
    transaction_type: str
    transaction_id: str

    model_config = {"frozen": True}


class WalletFundedEvent(DomainEvent[WalletFundedPayload]):
    _event_name: ClassVar[str] = "funded"
    _group: ClassVar[str] = "wallet"

    @classmethod
    def create(cls, txn: "Transaction"):
        return cls(
            aggregate_id=str(txn.id),
            payload=WalletFundedPayload(
                amount=txn.amount,
                user_id=str(txn.user_id),
                transaction_type=txn.transaction_type,
                transaction_id=str(txn.id),
            ),
        )

    class Config:
        frozen = True
