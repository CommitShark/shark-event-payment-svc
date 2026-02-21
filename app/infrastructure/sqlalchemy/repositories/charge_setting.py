from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.domain.entities import ChargeSetting
from app.domain.repositories import IChargeSettingRepository
from app.infrastructure.sqlalchemy.models import (
    SqlAlchemyChargeSetting,
    SqlAlchemyChargeSettingVersion,
)
from app.shared.errors import AppError


class SqlAlchemyChargeSettingRepository(IChargeSettingRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def get_by_id(
        self,
        charge_setting_id: UUID,
    ) -> ChargeSetting:
        result = await self._session.execute(
            select(SqlAlchemyChargeSetting).where(
                SqlAlchemyChargeSetting.charge_setting_id == charge_setting_id,
            ),
        )

        entity = result.scalars().one_or_none()

        if entity is not None:
            return entity.to_domain()

        raise AppError(f"Charge not found", 404)

    async def get_by_type(
        self,
        charge_type: str,
    ) -> ChargeSetting:
        result = await self._session.execute(
            select(SqlAlchemyChargeSetting).where(
                SqlAlchemyChargeSetting.charge_type == charge_type,
            ),
        )

        entity = result.scalars().one_or_none()

        if entity is not None:
            return entity.to_domain()

        raise AppError(f"Charge not found", 404)

    def save(self, charge_setting: ChargeSetting) -> None:
        entity = SqlAlchemyChargeSetting.from_domain(charge_setting)
        self._session.add(entity)

    async def list_all(self, active_only: bool = True) -> list[ChargeSetting]:
        stmt = select(SqlAlchemyChargeSetting)

        if active_only:
            stmt = stmt.where(SqlAlchemyChargeSetting.is_active == True)

        result = await self._session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_domain() for entity in entities]

    async def delete_all(self) -> None:
        await self._session.execute(delete(SqlAlchemyChargeSettingVersion))
        await self._session.execute(delete(SqlAlchemyChargeSetting))
