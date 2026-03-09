from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

from .extra import ExtraOrderIntent


class GetChargeReqDto(BaseModel):
    ticket_type_id: UUID
    slug: str
    quantity: int
    extras: list[ExtraOrderIntent] | None = None


class PublicGetChargeReqDto(GetChargeReqDto):
    user_id: UUID


class ChargeDto(BaseModel):
    base_amount: Decimal
    charge_setting_id: str | None = None
    version_id: str | None = None
    version_number: int | None = None
    calculated_charge: str | None = None
    percentage_rate: str | None = None
    signature: str | None = None
    charge_group: str | None = None


class GetChargeResDto(BaseModel):
    charges: list[ChargeDto]
    signature: str
