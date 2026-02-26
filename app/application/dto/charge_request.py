from pydantic import BaseModel
from decimal import Decimal


class GetChargeReqDto(BaseModel):
    charge_type: str
    ticket_type_id: str


class GetChargeResDto(BaseModel):
    base_amount: Decimal
    charge_setting_id: str | None = None
    version_id: str | None = None
    version_number: int | None = None
    calculated_charge: str | None = None
    percentage_rate: str | None = None
    signature: str | None = None
