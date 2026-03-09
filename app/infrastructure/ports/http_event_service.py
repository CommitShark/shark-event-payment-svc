from uuid import UUID

from app.domain.dto.event import ExtraDto
from app.utils.external_api_client import ExternalAPIClient
from app.domain.ports import IEventService


class HttpEventService(IEventService):
    def __init__(self, client: ExternalAPIClient) -> None:
        self.client = client

    async def get_active_extra_for_ticket(
        self,
        extra_id: UUID,
        extra_version: int,
        ticket_type_id: UUID,
    ) -> ExtraDto | None:
        print(
            f"get_active_extra_for_ticket: {extra_id}, {extra_version}, {ticket_type_id}"
        )

        try:
            endpoint = f"/system/extras/{extra_id}/ticket"
            result = await self.client._get(
                endpoint=endpoint,
                params={
                    "extra_version": extra_version,
                    "ticket_type_id": ticket_type_id,
                },
            )

            if not result:
                return None

            return ExtraDto.model_validate(result)
        except Exception as e:
            print(f"Error: {str(e)}")
            raise
