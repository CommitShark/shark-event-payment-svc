from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import (
    IChargeSettingRepository,
    IChargeSettingVersionRepository,
)
from app.infrastructure.sqlalchemy.repositories import (
    SqlAlchemyChargeSettingRepository,
    SqlAlchemyChargeSettingVersionRepository,
)


def get_charge_setting_repo(session: AsyncSession) -> IChargeSettingRepository:
    return SqlAlchemyChargeSettingRepository(session)


def get_charge_setting_version_repo(
    session: AsyncSession,
) -> IChargeSettingVersionRepository:
    return SqlAlchemyChargeSettingVersionRepository(session)
