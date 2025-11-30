from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional, Any
from sqlalchemy import (
    UUID,
    String,
    DateTime,
    Numeric,
    JSON,
)

from uuid import UUID as PyUUID

from app.domain.entities import (
    TransactionDirection,
    Transaction,
    TransactionSettlementStatus,
    TransactionSource,
    TransactionType,
    ChargeData,
    SettlementData,
)

from ..session import Base


class SqlAlchemyTransaction(Base):
    __tablename__ = "transactions"

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
    )

    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    resource: Mapped[str] = mapped_column(
        String,
        nullable=True,
    )

    resource_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    reference: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
    )

    source: Mapped[TransactionSource] = mapped_column(String, nullable=False)

    occurred_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    charge_data: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
    )

    settlement_status: Mapped[TransactionSettlementStatus] = mapped_column(
        String,
        nullable=False,
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        String,
        nullable=False,
    )

    transaction_direction: Mapped[TransactionDirection] = mapped_column(
        String,
        nullable=False,
    )

    settlement_data: Mapped[list[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, name="metadata"
    )

    @classmethod
    def from_domain(cls, data: Transaction) -> "SqlAlchemyTransaction":
        return cls(
            id=data.id,
            amount=data.amount,
            user_id=data.user_id,
            resource=data.resource,
            resource_id=data.resource_id,
            reference=data.reference,
            source=data.source,
            occurred_on=data.occurred_on,
            charge_data=(
                data.charge_data.model_dump_json() if data.charge_data else None
            ),
            settlement_status=data.settlement_status,
            transaction_type=data.transaction_type,
            transaction_direction=data.transaction_direction,
            settlement_data=[s.model_dump() for s in data.settlement_data],
            created_at=data.created_at,
            metadata_=data.metadata,
        )

    def to_domain(self) -> "Transaction":
        return Transaction(
            id=self.id,
            amount=self.amount,
            user_id=self.user_id,
            resource=self.resource,
            resource_id=self.resource_id,
            reference=self.reference,
            source=self.source,
            occurred_on=self.occurred_on,
            charge_data=(
                ChargeData.model_validate_json(self.charge_data)
                if self.charge_data
                else None
            ),
            settlement_status=self.settlement_status,
            transaction_type=self.transaction_type,
            transaction_direction=self.transaction_direction,
            settlement_data=[
                SettlementData.model_validate(s) for s in self.settlement_data
            ],
            created_at=self.created_at,
            metadata=self.metadata_,
        )
