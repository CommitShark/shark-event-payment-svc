from pydantic import BaseModel, Field
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

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, "f"),
        }
    }


class SettlementData(BaseModel):
    amount: Decimal = Field(gt=0)
    recipient_user: UUID
    transaction_type: TransactionType
    role: str

    model_config = {
        "json_encoders": {
            Decimal: lambda v: format(v, "f"),
        }
    }


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
