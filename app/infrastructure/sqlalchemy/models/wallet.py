from uuid import UUID as PyUUID
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    UUID,
    String,
    Numeric,
)

from app.domain.entities import Wallet

from ..session import Base


class SqlAlchemyWallet(Base):
    __tablename__ = "wallets"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )

    pending_balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )

    txn_pin: Mapped[Optional[str]] = mapped_column(
        String(4),
        nullable=False,
    )

    @classmethod
    def from_domain(cls, data: Wallet) -> "SqlAlchemyWallet":
        return cls(
            id=data.id,
            balance=data.balance,
            user_id=data.user_id,
            pending_balance=data.pending_balance,
            txn_pin=data.txn_pin,
        )

    def to_domain(self) -> "Wallet":
        return Wallet(
            id=self.id,
            balance=self.balance,
            user_id=self.user_id,
            pending_balance=self.pending_balance,
            txn_pin=self.txn_pin,
        )
