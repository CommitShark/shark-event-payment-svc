from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Any

from app.shared.errors import AppError
from ..events import TransactionCreatedEvent, PurchaseSettledEvent, NotifyEvent
from ..events.base import DomainEvent
from .value_objects import (
    TransactionDirection,
    TransactionSettlementStatus,
    TransactionSource,
    TransactionType,
    ChargeData,
    SettlementData,
)


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
    parent_id: Optional[UUID] = None

    _events: list[DomainEvent[Any]] = []

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, "f"),
        }
    }

    @property
    def description(self):
        # --- PURCHASES ---
        if self.transaction_type == "purchase":
            return f"Purchase made for {self.resource}"

        # --- SALES (money received for delivering a resource) ---
        if self.transaction_type == "sale":
            return f"Payment received for {self.resource} sale"

        # --- COMMISSIONS ---
        if self.transaction_type == "commission":
            return f"Commission received for {self.resource}"

        # --- WALLET FUNDING ---
        if self.transaction_type == "wallet_funding":
            if self.source == "payment_provider":
                return "Wallet funded via payment provider"
            if self.source == "wallet":
                return "Wallet-to-wallet transfer received"
            return "Wallet funded"

        # --- WITHDRAWALS ---
        if self.transaction_type == "withdrawal":
            return "Withdrawal from wallet balance"

        # --- FALLBACK ---
        return "Transaction"

    @property
    def events(self):
        events_ = list(self._events)
        self._events.clear()
        return events_

    def mark_as_failed(self, reason: str) -> Decimal | None:
        if self.transaction_type == "withdrawal" and (
            self.settlement_status == "pending"
            or self.settlement_status == "processing"
        ):
            mode = (self.metadata or {}).get("mode")

            if mode == "manual":
                # Refund user and create a failed notification then return refundable amount
                self.settlement_status = "failed"
                self.metadata = self.metadata or {}
                self.metadata["failed_on"] = datetime.now(timezone.utc).isoformat()

                self._events.append(
                    NotifyEvent.manual_withdrawal_failed(
                        self,
                        reason,
                    )
                )

                return self.amount + (
                    self.charge_data.charge_amount if self.charge_data else 0
                )

        raise AppError(
            "MarkAsFailed: Not Implemented", 500, {"txn": self.model_dump_json()}
        )

    def complete_settlement(self):
        self.settlement_status = "completed"
        if self.transaction_type == "purchase":
            self._events.append(PurchaseSettledEvent.create(self))
        elif self.transaction_type == "withdrawal":
            self._events.append(NotifyEvent.withdrawal_complete(self))

    def add_settlement(self, data: SettlementData):
        if self.settlement_status != "pending":
            raise AppError(
                "Transaction state is invalid. Cannot modify settlement", 409
            )
        self.settlement_data.append(data)

    def create_settlement_transactions(self) -> list["Transaction"]:
        return [
            Transaction.create(
                amount=s.amount,
                user_id=s.recipient_user,
                resource=self.resource,
                resource_id=self.resource_id,
                occurred_on=datetime.now(timezone.utc),
                transaction_type=s.transaction_type,
                source=self.source,
                reference=uuid4(),
                settlement_status="pending",
                parent_id=self.id,
            )
            for s in self.settlement_data
        ]

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
        parent_id: Optional[UUID] = None,
    ) -> "Transaction":

        # Automatic direction logic
        if transaction_direction is None:
            direction_map: dict[TransactionType, TransactionDirection] = {
                "purchase": "debit",
                "wallet_funding": "credit",
                "sale": "credit",
                "commission": "credit",
                "withdrawal": "debit",
            }
            transaction_direction = direction_map[transaction_type]

        txn = Transaction(
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
            parent_id=parent_id,
        )

        txn._events.append(TransactionCreatedEvent.create(txn))

        return txn
