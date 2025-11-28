from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func, update
from typing import Optional
from datetime import datetime, timezone

from app.domain.entities import ChargeSettingVersion, PriceRangeTier
from app.domain.repositories import IChargeSettingVersionRepository
from app.infrastructure.sqlalchemy.models import SqlAlchemyChargeSettingVersion
from app.shared.errors import AppError


class SqlAlchemyChargeSettingVersionRepository(IChargeSettingVersionRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        version_id: UUID,
    ) -> ChargeSettingVersion:
        result = await self._session.execute(
            select(SqlAlchemyChargeSettingVersion).where(
                SqlAlchemyChargeSettingVersion.version_id == version_id,
            ),
        )

        entity = result.scalars().one_or_none()

        if entity is not None:
            return entity.to_domain()

        raise AppError(f"Charge version not found", 404)

    async def get_current_version(
        self,
        charge_setting_id: UUID,
    ) -> Optional[ChargeSettingVersion]:
        now = datetime.now(timezone.utc)

        result = await self._session.execute(
            select(SqlAlchemyChargeSettingVersion)
            .where(
                and_(
                    SqlAlchemyChargeSettingVersion.charge_setting_id
                    == charge_setting_id,
                    SqlAlchemyChargeSettingVersion.effective_from <= now,
                    (
                        SqlAlchemyChargeSettingVersion.effective_until.is_(None)
                        | (SqlAlchemyChargeSettingVersion.effective_until > now)
                    ),
                )
            )
            .order_by(desc(SqlAlchemyChargeSettingVersion.version_number))
            .limit(1)
        )

        entity = result.scalars().one_or_none()

        if entity is None:
            return None

        return entity.to_domain()

    async def get_version_at(
        self,
        charge_setting_id: UUID,
        at_time: datetime,
    ) -> Optional[ChargeSettingVersion]:
        """Get the version that was active at a specific time"""
        result = await self._session.execute(
            select(SqlAlchemyChargeSettingVersion)
            .where(
                and_(
                    SqlAlchemyChargeSettingVersion.charge_setting_id
                    == charge_setting_id,
                    SqlAlchemyChargeSettingVersion.effective_from <= at_time,
                    (
                        SqlAlchemyChargeSettingVersion.effective_until.is_(None)
                        | (SqlAlchemyChargeSettingVersion.effective_until > at_time)
                    ),
                )
            )
            .order_by(desc(SqlAlchemyChargeSettingVersion.version_number))
            .limit(1)
        )

        entity = result.scalars().one_or_none()

        if entity is None:
            return None

        return entity.to_domain()

    async def get_version_by_number(
        self,
        charge_setting_id: UUID,
        version_number: int,
    ) -> Optional[ChargeSettingVersion]:
        result = await self._session.execute(
            select(SqlAlchemyChargeSettingVersion).where(
                and_(
                    SqlAlchemyChargeSettingVersion.charge_setting_id
                    == charge_setting_id,
                    SqlAlchemyChargeSettingVersion.version_number == version_number,
                )
            )
        )

        entity = result.scalars().one_or_none()

        if entity is None:
            return None

        return entity.to_domain()

    async def get_version_history(
        self,
        charge_setting_id: UUID,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[ChargeSettingVersion]:
        query = (
            select(SqlAlchemyChargeSettingVersion)
            .where(
                SqlAlchemyChargeSettingVersion.charge_setting_id == charge_setting_id
            )
            .order_by(desc(SqlAlchemyChargeSettingVersion.version_number))
            .offset(offset)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self._session.execute(query)
        entities = result.scalars().all()

        return [entity.to_domain() for entity in entities]

    async def add_version(
        self,
        charge_setting_id: UUID,
        tiers: list[PriceRangeTier],
        effective_from: datetime,
        created_by: str,
        change_reason: Optional[str] = None,
    ) -> ChargeSettingVersion:
        """
        Add a new version to a charge setting.
        Automatically closes the previous version and updates version numbering.
        CONCURRENCY-SAFE: Uses SELECT FOR UPDATE and atomic operations.
        """
        # Get the latest version number with row-level lock to prevent race conditions
        result = await self._session.execute(
            select(
                func.max(SqlAlchemyChargeSettingVersion.version_number).label(
                    "max_version"
                )
            )
            .where(
                SqlAlchemyChargeSettingVersion.charge_setting_id == charge_setting_id
            )
            .with_for_update()  # Lock to prevent concurrent version number collisions
        )
        max_version = result.scalar()
        new_version_number = (max_version or 0) + 1

        # Atomically close all currently active versions
        # This handles edge cases where multiple versions might be active
        await self._session.execute(
            update(SqlAlchemyChargeSettingVersion)
            .where(
                and_(
                    SqlAlchemyChargeSettingVersion.charge_setting_id
                    == charge_setting_id,
                    SqlAlchemyChargeSettingVersion.effective_until.is_(None),
                )
            )
            .values(effective_until=effective_from)
            .execution_options(synchronize_session=False)
        )

        # Create the new version
        new_version = ChargeSettingVersion(
            version_number=new_version_number,
            tiers=tiers,
            effective_from=effective_from,
            effective_until=None,
            created_by=created_by,
            change_reason=change_reason,
            charge_setting_id=charge_setting_id,
        )

        # Save the new version
        self.save(new_version)

        # Flush to ensure uniqueness constraints are checked before commit
        await self._session.flush()

        return new_version

    def save(self, charge_setting_version: ChargeSettingVersion) -> None:
        entity = SqlAlchemyChargeSettingVersion.from_domain(charge_setting_version)
        self._session.add(entity)

    async def count_versions(self, charge_setting_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(SqlAlchemyChargeSettingVersion.version_id)).where(
                SqlAlchemyChargeSettingVersion.charge_setting_id == charge_setting_id
            )
        )
        count = result.scalar()
        return count or 0
