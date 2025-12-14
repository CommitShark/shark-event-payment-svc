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
        session: AsyncSession | None = None,
    ) -> None:
        self._session: AsyncSession | None = session

    def set_session(self, session: AsyncSession) -> None:
        if self._session is not None:
            raise AppError("Session is already set", 500)
        self._session = session

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise AppError("Session is not set", 500)
        return self._session

    async def save(self, w: Wallet) -> None:
        await self.session.merge(SqlAlchemyWallet.from_domain(w))
        await self.session.flush()

    async def get_by_user_or_create(
        self,
        u: UUID,
        lock_for_update: bool = False,
    ) -> Wallet:
        result = await self.session.execute(
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
