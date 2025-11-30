from typing import Protocol
from abc import abstractmethod

from ..entities import Transaction


class ITransactionRepository(Protocol):
    @abstractmethod
    def save(self, txn: Transaction) -> None: ...
