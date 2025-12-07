from typing import Protocol, Optional
from decimal import Decimal
from abc import abstractmethod

from ..dto import ExternalTransaction, PersonalAccount, BankItem


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

    @abstractmethod
    async def resolve_personal_bank(
        self, bank: str, account: str
    ) -> PersonalAccount: ...

    @abstractmethod
    async def list_banks(self) -> list[BankItem]: ...

    @abstractmethod
    async def withdraw(
        self,
        amount: Decimal,
        recipient_id: str,
        ref: str,
        reason: str,
    ): ...

    @abstractmethod
    async def add_recipient(
        self,
        account_number: str,
        account_name: str,
        bank_code: str,
    ) -> str: ...
