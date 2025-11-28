from typing import Protocol, List

from app.domain.events.base import DomainEvent


class IEventHandler(Protocol):
    events: List[type[DomainEvent]]

    async def handle(self, event: DomainEvent): ...
