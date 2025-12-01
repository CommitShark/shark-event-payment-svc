from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domain.entities.transaction import Transaction
from app.domain.repositories import ITransactionRepository


from ..models import SqlAlchemyTransaction


class SqlAlchemyTransactionRepository(ITransactionRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def save(self, txn: Transaction) -> None:
        entity = SqlAlchemyTransaction.from_domain(txn)
        # print(entity.amount, entity.charge_data, entity.settlement_data)
        await self._session.merge(entity)
        await self._session.flush()

    async def get_by_reference_or_none(
        self,
        reference: UUID,
        lock_for_update: bool = False,
    ) -> Transaction | None:
        result = await self._session.execute(
            (
                select(SqlAlchemyTransaction).where(
                    SqlAlchemyTransaction.reference == reference,
                )
                if not lock_for_update
                else select(SqlAlchemyTransaction)
                .where(
                    SqlAlchemyTransaction.reference == reference,
                )
                .with_for_update()
            ),
        )

        entity = result.scalars().one_or_none()

        return entity.to_domain() if entity else None
