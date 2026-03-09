from pydantic import BaseModel, Field, field_serializer
from typing import List
from decimal import Decimal
from uuid import UUID


class ExtraOrderDto(BaseModel):
    extra_id: UUID
    extra_version: int
    quantity: int = Field(ge=0)
    unit_price: Decimal
    recipient: UUID

    @field_serializer("recipient")
    def serialize_recipient(self, v: UUID):
        return str(v)

    @field_serializer("extra_id")
    def serialize_extra_id(self, v: UUID):
        return str(v)

    @field_serializer("unit_price")
    def serialize_unit_price(self, v: Decimal):
        return format(v, "f")

    @property
    def cost(self):
        return self.unit_price * self.quantity

    @staticmethod
    def calculate_total(orders: List["ExtraOrderDto"]) -> Decimal:
        return sum((order.cost for order in orders), start=Decimal("0"))
