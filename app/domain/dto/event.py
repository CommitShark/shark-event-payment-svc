from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal


class ExtraDto(BaseModel):
    id: UUID
    name: str
    version: int
    price: Decimal
    quantity_available: int
