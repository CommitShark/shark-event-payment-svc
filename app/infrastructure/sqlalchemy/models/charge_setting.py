from uuid import UUID as PyUUID
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    UUID,
    String,
    DateTime,
    Boolean,
)

from app.domain.entities import ChargeSetting

from app.infrastructure.sqlalchemy.session import Base


class SqlAlchemyChargeSetting(Base):
    __tablename__ = "charge_settings"

    charge_setting_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[str] = mapped_column(String, nullable=True)

    charge_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    @classmethod
    def from_domain(cls, data: ChargeSetting) -> "SqlAlchemyChargeSetting":
        return cls(
            charge_setting_id=data.charge_setting_id,
            name=data.name,
            description=data.description,
            charge_type=data.charge_type,
            created_at=data.created_at,
            updated_at=data.updated_at,
            is_active=data.is_active,
        )

    def to_domain(self) -> "ChargeSetting":
        return ChargeSetting(
            charge_setting_id=self.charge_setting_id,
            name=self.name,
            description=self.description,
            charge_type=self.charge_type,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
        )
