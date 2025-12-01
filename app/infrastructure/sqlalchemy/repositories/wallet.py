from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.entities.wallet import Wallet
from app.domain.repositories import IWalletRepository
from app.shared.errors import AppError
from ..models import SqlAlchemyWallet


class SqlAlchemyWalletRepository(IWalletRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(self, w: Wallet) -> None:
        await self._session.merge(SqlAlchemyWallet.from_domain(w))
        await self._session.flush()

    async def get_by_user_or_create(
        self,
        u: UUID,
        lock_for_update: bool = False,
    ) -> Wallet:
        result = await self._session.execute(
            (
                select(SqlAlchemyWallet).where(
                    SqlAlchemyWallet.user_id == u,
                )
                if not lock_for_update
                else select(SqlAlchemyWallet)
                .where(
                    SqlAlchemyWallet.user_id == u,
                )
                .with_for_update()
            ),
        )

        entity = result.scalar()

        if entity:
            return entity.to_domain()

        domain = Wallet(user_id=u)
        await self.save(domain)

        return domain
