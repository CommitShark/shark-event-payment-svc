from uuid import UUID as PyUUID
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    UUID,
    String,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)

from app.domain.entities import ChargeSettingVersion, PriceRangeTier

from app.infrastructure.sqlalchemy.session import Base


class SqlAlchemyChargeSettingVersion(Base):
    __tablename__ = "charge_setting_versions"

    __table_args__ = (
        # Prevent duplicate version numbers per charge setting
        UniqueConstraint(
            "charge_setting_id",
            "version_number",
            name="uq_charge_setting_version_number",
        ),
        # Optimize queries for current version lookup
        Index(
            "ix_charge_setting_active_version",
            "charge_setting_id",
            "effective_from",
            "effective_until",
        ),
    )

    version_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    tiers: Mapped[list[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
    )

    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    effective_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_by: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    change_reason: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
    )

    charge_setting_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("charge_settings.charge_setting_id", ondelete="RESTRICT"),
        nullable=False,
    )

    @classmethod
    def from_domain(
        cls, data: ChargeSettingVersion
    ) -> "SqlAlchemyChargeSettingVersion":
        return cls(
            version_id=data.version_id,
            version_number=data.version_number,
            tiers=[tier.model_dump() for tier in data.tiers],
            effective_from=data.effective_from,
            effective_until=data.effective_until,
            created_at=data.created_at,
            created_by=data.created_by,
            change_reason=data.change_reason,
            charge_setting_id=data.charge_setting_id,
        )

    def to_domain(self) -> "ChargeSettingVersion":
        return ChargeSettingVersion(
            version_id=self.version_id,
            version_number=self.version_number,
            tiers=[PriceRangeTier.model_validate(tier) for tier in self.tiers],
            effective_from=self.effective_from,
            effective_until=self.effective_until,
            created_at=self.created_at,
            created_by=self.created_by,
            change_reason=self.change_reason,
            charge_setting_id=self.charge_setting_id,
        )
