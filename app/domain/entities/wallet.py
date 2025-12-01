from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional


class Wallet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    balance: Decimal = Field(ge=0, default=Decimal(0))
    pending_balance: Decimal = Field(ge=0, default=Decimal(0))
    txn_pin: Optional[str] = None

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            Decimal: lambda v: format(v, "f"),
        },
    }

    def can_withdraw(self, amount: Decimal) -> bool:
        return self.balance >= amount

    def deposit(self, amount: Decimal):
        """Instant deposit to available balance."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount

    def withdraw(self, amount: Decimal):
        """Withdraw immediately from available balance."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if not self.can_withdraw(amount):
            raise ValueError("Insufficient balance")
        self.balance -= amount

    def hold_funds(self, amount: Decimal):
        """
        Move available funds → pending.
        Useful for reservations, ticket purchases, escrow, etc.
        """
        if amount <= 0:
            raise ValueError("Hold amount must be positive")
        if not self.can_withdraw(amount):
            raise ValueError("Insufficient balance to hold funds")
        self.balance -= amount
        self.pending_balance += amount

    def release_hold(self, amount: Decimal):
        """Move pending funds → available."""
        if amount <= 0:
            raise ValueError("Release amount must be positive")
        if self.pending_balance < amount:
            raise ValueError("Insufficient pending funds to release")
        self.pending_balance -= amount
        self.balance += amount

    def set_pin(self, pin: str):
        """Assign transaction PIN."""
        if len(pin) < 4:
            raise ValueError("PIN must be at least 4 digits")
        self.txn_pin = pin

    def verify_pin(self, pin: str) -> bool:
        """Verify transaction PIN."""
        return self.txn_pin == pin
