from typing import Protocol
from typing import Type, Callable
from app.domain.events.base import DomainEvent


class IEventBus(Protocol):
    async def subscribe(self, event_type: Type[DomainEvent], handler: Callable): ...

    async def publish(self, event: DomainEvent): ...
