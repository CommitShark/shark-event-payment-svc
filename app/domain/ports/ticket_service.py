from typing import Protocol
from abc import abstractmethod
from decimal import Decimal


class ITicketService(Protocol):
    @abstractmethod
    async def get_ticket_price(self, ticket_type_id: str) -> Decimal: ...

    @abstractmethod
    async def reservation_is_valid(
        self, reservation_id: str
    ) -> tuple[bool, str | None]: ...

    @abstractmethod
    async def mark_reservation_as_paid(self, reservation_id: str, amount: Decimal): ...
