from typing import Protocol
from abc import abstractmethod
from decimal import Decimal


class ITicketService(Protocol):
    @abstractmethod
    async def get_ticket_price(self, ticket_type_id: str) -> Decimal: ...
