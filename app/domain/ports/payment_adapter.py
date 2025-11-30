from typing import Protocol, Optional
from decimal import Decimal
from abc import abstractmethod

from ..dto import ExternalTransaction


class IPaymentAdapter(Protocol):
    @abstractmethod
    async def create_checkout_link(
        self,
        email: str,
        amount: Decimal,
        callback_url: str,
        reference: str,
        metadata: Optional[dict] = None,
    ) -> str: ...

    @abstractmethod
    async def get_valid_transaction(self, reference: str) -> ExternalTransaction: ...
