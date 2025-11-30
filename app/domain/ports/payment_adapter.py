from typing import Protocol, Optional
from decimal import Decimal
from abc import abstractmethod


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
    async def is_transaction_complete(self, reference: str) -> bool: ...
