import logging
from datetime import datetime
from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domain.dto.transaction import TransactionFilter
from app.domain.entities.transaction import Transaction
from app.domain.repositories import ITransactionRepository
from app.shared.errors import AppError


from ..models import SqlAlchemyTransaction


logger = logging.getLogger("[SqlAlchemyTransactionRepository]")


class SqlAlchemyTransactionRepository(ITransactionRepository):
    def __init__(
        self,
        session: AsyncSession | None = None,
    ) -> None:
        self._session: AsyncSession | None = session

    def set_session(self, session: AsyncSession) -> None:
        logger.info("Set session")
        if self._session is not None:
            raise AppError("Session is already set", 500)
        self._session = session

    @property
    def safe_session(self) -> AsyncSession:
        if self._session is None:
            raise AppError("Session is not set", 500)
        return self._session

    async def save(self, txn: Transaction) -> None:
        entity = SqlAlchemyTransaction.from_domain(txn)
        # print(entity.amount, entity.charge_data, entity.settlement_data)
        await self.safe_session.merge(entity)
        await self.safe_session.flush()

    async def get_by_id(
        self,
        id: UUID,
        lock_for_update: bool = False,
    ) -> Transaction:
        result = await self.safe_session.execute(
            (
                select(SqlAlchemyTransaction).where(
                    SqlAlchemyTransaction.id == id,
                )
                if not lock_for_update
                else select(SqlAlchemyTransaction)
                .where(
                    SqlAlchemyTransaction.id == id,
                )
                .with_for_update()
            ),
        )

        entity = result.scalars().one_or_none()

        if entity:
            return entity.to_domain()

        raise AppError(f"Transaction {id} not found", 404)

    async def get_by_reference_or_none(
        self,
        reference: UUID,
        lock_for_update: bool = False,
    ) -> Transaction | None:
        result = await self.safe_session.execute(
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

    async def query_by_user(
        self,
        offset: int,
        limit: int,
        user_id: UUID,
    ) -> tuple[list[Transaction], int]:
        base_stmt = select(SqlAlchemyTransaction).where(
            SqlAlchemyTransaction.user_id == user_id
        )

        # -----------------------
        # 1. Get total count
        # -----------------------
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.safe_session.execute(count_stmt)).scalar_one()

        # -----------------------
        # 2. Get paginated data
        # -----------------------
        data_stmt = (
            base_stmt.order_by(SqlAlchemyTransaction.occurred_on.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.safe_session.execute(data_stmt)
        entities = result.scalars().all()

        return [entity.to_domain() for entity in entities], total

    async def query(
        self,
        offset: int,
        limit: int,
        filter: TransactionFilter | None = None,
    ) -> tuple[List[Transaction], int]:
        base_stmt = select(SqlAlchemyTransaction)

        if filter:
            if filter.status:
                base_stmt = base_stmt.where(
                    SqlAlchemyTransaction.settlement_status == filter.status
                )

            if filter.type:
                base_stmt = base_stmt.where(
                    SqlAlchemyTransaction.transaction_type == filter.type
                )

        # -----------------------
        # 1. Get total count
        # -----------------------
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = (await self.safe_session.execute(count_stmt)).scalar_one()

        # -----------------------
        # 2. Get paginated data
        # -----------------------
        data_stmt = (
            base_stmt.order_by(SqlAlchemyTransaction.occurred_on.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.safe_session.execute(data_stmt)
        entities = result.scalars().all()

        return [entity.to_domain() for entity in entities], total

    async def find_due_scheduled(
        self,
        date: datetime,
    ) -> List[Transaction]:
        stmt = (
            select(SqlAlchemyTransaction)
            .where(SqlAlchemyTransaction.settlement_status == "scheduled")
            .where(SqlAlchemyTransaction.delayed_settlement_until <= date)
            .limit(20)  # Batch Size for processing due settlements
        )

        result = await self.safe_session.execute(stmt)
        entities = result.scalars().all()

        return [entity.to_domain() for entity in entities]
