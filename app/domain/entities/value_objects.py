from pydantic import BaseModel, Field, field_serializer
from uuid import UUID
from decimal import Decimal
from typing import Literal
from datetime import datetime


TransactionSettlementStatus = Literal[
    "pending",
    "failed",
    "completed",
    "not_applicable",
    "processing",
    "scheduled",
]
TransactionType = Literal[
    "purchase",
    "wallet_funding",
    "sale",
    "commission",
    "withdrawal",
    "fee",
]
TransactionDirection = Literal["credit", "debit"]
TransactionSource = Literal["wallet", "payment_provider"]


class ChargeData(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    charge_amount: Decimal = Field(gt=0)
    sponsored: bool
    charge_group: str | None = None

    @field_serializer("charge_amount")
    def serialize_decimal(self, v: Decimal):
        return format(v, "f")


class SettlementDataResource(BaseModel):
    resource: str
    resource_id: UUID | None = None

    @field_serializer("resource_id")
    def serialize_uuid(self, v: UUID | None):
        return str(v) if v else None


class SettlementData(BaseModel):
    amount: Decimal = Field(gt=0)
    recipient_user: UUID
    transaction_type: TransactionType
    role: str
    resource: SettlementDataResource | None = None
    metadata: dict | None = None

    @field_serializer("amount")
    def serialize_amount(self, v: Decimal):
        return format(v, "f")

    @field_serializer("recipient_user")
    def serialize_recipient_user(self, v: UUID):
        return str(v)


class BankDetails(BaseModel):
    account_name: str
    account_number: str
    bank_name: str
    bank_code: str
    updated_at: datetime

    def build_dest(self) -> str:
        """
        Returns a human-friendly destination string, e.g.:

        '0012345678 • Test User • GTBank'
        '0012345678 • GTBank'
        '0012345678'
        """
        parts: list[str] = []

        # Required
        parts.append(self.account_number)

        # Optional
        if self.account_name:
            parts.append(self.account_name)

        # Optional
        if self.bank_name:
            parts.append(self.bank_name)

        # Join gracefully with separators
        return " • ".join(parts)
