from uuid import UUID
from pydantic import BaseModel


class ExtraOrderIntent(BaseModel):
    extra_id: UUID
    extra_version: int
    quantity: int
    recipient_id: UUID

    class Config:
        frozen = True
        json_encoders = {
            UUID: str,
        }
