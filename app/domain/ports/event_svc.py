from typing import Protocol
from uuid import UUID

from app.domain.dto.event import ExtraDto


class IEventService(Protocol):
    async def get_active_extra_for_ticket(
        self,
        extra_id: UUID,
        extra_version: int,
        ticket_type_id: UUID,
    ) -> ExtraDto | None: ...
