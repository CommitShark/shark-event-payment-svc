from typing import Protocol
from abc import abstractmethod
from uuid import UUID

from ..entities import Wallet


class IWalletRepository(Protocol):
    @abstractmethod
    async def save(self, w: Wallet) -> None: ...

    @abstractmethod
    async def get_by_user_or_create(
        self,
        u: UUID,
        lock_for_update: bool = False,
    ) -> Wallet: ...
