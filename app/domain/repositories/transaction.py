from typing import Protocol, List
from uuid import UUID
from abc import abstractmethod

from ..entities import Transaction
from ..dto import TransactionFilter


class ITransactionRepository(Protocol):
    @abstractmethod
    async def save(self, txn: Transaction) -> None: ...

    @abstractmethod
    async def get_by_reference_or_none(
        self,
        reference: UUID,
        lock_for_update: bool = False,
    ) -> Transaction | None: ...

    @abstractmethod
    async def get_by_id(
        self,
        reference: UUID,
        lock_for_update: bool = False,
    ) -> Transaction: ...

    @abstractmethod
    async def query_by_user(
        self,
        offset: int,
        limit: int,
        user_id: UUID,
    ) -> tuple[List[Transaction], int]: ...

    @abstractmethod
    async def query(
        self,
        offset: int,
        limit: int,
        filter: TransactionFilter | None = None,
    ) -> tuple[List[Transaction], int]: ...
