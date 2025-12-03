from typing import Protocol, List
from uuid import UUID
from abc import abstractmethod

from ..entities import Transaction


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
    async def query_by_user(
        self,
        offset: int,
        limit: int,
        user_id: UUID,
    ) -> tuple[List[Transaction], int]: ...
