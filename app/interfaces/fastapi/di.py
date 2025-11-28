from fastapi import Depends
from typing import Annotated, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.sqlalchemy.session import get_async_session
from app.domain.repositories import (
    IChargeSettingRepository,
    IChargeSettingVersionRepository,
)
from app.infrastructure.sqlalchemy.repositories import (
    SqlAlchemyChargeSettingRepository,
    SqlAlchemyChargeSettingVersionRepository,
)
from app.domain.services import ChargeCalculationService
from app.application.use_cases import RequestChargeUseCase


async def get_db() -> AsyncIterator[AsyncSession]:
    async with get_async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_charge_setting_repository(
    session: DbSession,
) -> IChargeSettingRepository:
    return SqlAlchemyChargeSettingRepository(session)


ChargeSettingRepoDep = Annotated[
    IChargeSettingRepository,
    Depends(get_charge_setting_repository),
]


def get_charge_setting_version_repository(
    session: DbSession,
) -> IChargeSettingVersionRepository:
    return SqlAlchemyChargeSettingVersionRepository(session)


ChargeSettingVersionRepoDep = Annotated[
    IChargeSettingVersionRepository,
    Depends(get_charge_setting_version_repository),
]


def get_RequestChargeUseCase(
    charge_setting_repo: ChargeSettingRepoDep,
    version_repo: ChargeSettingVersionRepoDep,
):
    charge_calc_service = ChargeCalculationService(
        charge_setting_repo,
        version_repo,
    )
    return RequestChargeUseCase(
        charge_calc_service,
        charge_setting_repo,
    )


RequestChargeUseCaseDep = Annotated[
    RequestChargeUseCase, Depends(get_RequestChargeUseCase)
]
