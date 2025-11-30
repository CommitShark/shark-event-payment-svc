from typing import Protocol
from uuid import UUID
from abc import abstractmethod

from ..entities import Transaction


class ITransactionRepository(Protocol):
    @abstractmethod
    def save(self, txn: Transaction) -> None: ...

    @abstractmethod
    async def get_by_reference_or_none(
        self,
        reference: UUID,
        lock_for_update: bool = False,
    ) -> Transaction | None: ...
