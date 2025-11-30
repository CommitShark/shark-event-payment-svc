from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.transaction import Transaction
from app.domain.repositories import ITransactionRepository


from ..models import SqlAlchemyTransaction


class SqlAlchemyTransactionRepository(ITransactionRepository):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    def save(self, txn: Transaction) -> None:
        entity = SqlAlchemyTransaction.from_domain(txn)
        print(entity.amount, entity.charge_data, entity.settlement_data)
        self._session.add(entity)
