from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Literal

TransactionSettlementStatus = Literal[
    "pending", "in_progress", "failed", "completed", "not_applicable"
]
TransactionType = Literal[
    "purchase",
    "wallet_funding",
    "sale",
    "commission",
    "withdrawal",
]
TransactionDirection = Literal["credit", "debit"]
TransactionSource = Literal["wallet", "payment_provider"]


class ChargeData(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    charge_amount: Decimal = Field(gt=0)
    sponsored: bool


class SettlementData(BaseModel):
    amount: Decimal = Field(gt=0)
    recipient_user: UUID


# === Entity ===


class Transaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    amount: Decimal = Field(gt=0)
    user_id: UUID
    resource: str
    resource_id: UUID
    reference: UUID
    source: TransactionSource
    occurred_on: datetime
    charge_data: Optional[ChargeData] = None
    settlement_status: TransactionSettlementStatus
    transaction_type: TransactionType
    transaction_direction: TransactionDirection
    settlement_data: list[SettlementData] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[dict] = None

    @staticmethod
    def create(
        *,
        amount: Decimal,
        user_id: UUID,
        resource: str,
        resource_id: UUID,
        reference: UUID,
        occurred_on: datetime,
        transaction_type: TransactionType,
        source: TransactionSource,
        settlement_status: TransactionSettlementStatus = "pending",
        charge_data: Optional[ChargeData] = None,
        settlement_data: Optional[list[SettlementData]] = None,
        metadata: Optional[dict] = None,
        transaction_direction: Optional[TransactionDirection] = None,
    ) -> "Transaction":

        # Automatic direction logic
        if transaction_direction is None:
            direction_map: dict[TransactionType, TransactionDirection] = {
                "purchase": "debit",
                "wallet_funding": "credit",
                "sale": "credit",
                "commission": "debit",
            }
            transaction_direction = direction_map[transaction_type]

        return Transaction(
            amount=amount,
            user_id=user_id,
            resource=resource,
            resource_id=resource_id,
            reference=reference,
            occurred_on=occurred_on,
            settlement_status=settlement_status,
            transaction_type=transaction_type,
            transaction_direction=transaction_direction,
            charge_data=charge_data,
            settlement_data=settlement_data or [],
            metadata=metadata,
            source=source,
        )
