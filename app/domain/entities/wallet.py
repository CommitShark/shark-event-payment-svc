from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime, timezone
from app.shared.errors import AppError, ErrorCodes
import bcrypt  # type: ignore

from .value_objects import BankDetails


class Wallet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    balance: Decimal = Field(ge=0, default=Decimal(0))
    pending_balance: Decimal = Field(ge=0, default=Decimal(0))
    txn_pin: Optional[str] = None
    pin_updated_at: Optional[datetime] = None
    bank_details: Optional[BankDetails] = None

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {
            Decimal: lambda v: format(v, "f"),
        },
    }

    @property
    def has_pin(self):
        return self.txn_pin is not None

    def set_bank_details(self, bank: str, name: str, number: str):
        self.bank_details = BankDetails(
            account_name=name,
            account_number=number,
            bank=bank,
            updated_at=datetime.now(timezone.utc),
        )

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
        """Hash and store transaction PIN."""

        if len(pin) != 4:
            raise ValueError("PIN must be 4 digits long")

        # Hash the PIN
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pin.encode("utf-8"), salt)

        self.txn_pin = hashed.decode("utf-8")
        self.pin_updated_at = datetime.now(timezone.utc)

    def verify_pin(self, pin: str) -> bool:
        """Check if the provided PIN matches the stored hash."""
        if not self.txn_pin:
            return False

        return bcrypt.checkpw(pin.encode("utf-8"), self.txn_pin.encode("utf-8"))

    def change_pin(self, old_pin: str, new_pin: str):
        if not self.verify_pin(old_pin):
            raise AppError(
                "Incorrect transaction pin",
                400,
                error_code=ErrorCodes.INVALID_TXN_PIN,
            )

        self.set_pin(new_pin)
