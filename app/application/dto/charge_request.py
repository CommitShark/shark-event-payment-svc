from pydantic import BaseModel
from decimal import Decimal


class GetChargeReqDto(BaseModel):
    charge_type: str
    ticket_type_id: str


class GetChargeResDto(BaseModel):
    base_amount: Decimal
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    signature: str
