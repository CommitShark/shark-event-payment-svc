from pydantic import BaseModel, EmailStr


class CreateCheckoutReqDto(BaseModel):
    reservation_id: str
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    ticket_type_id: str
    slug: str
    email: EmailStr
    signature: str


class CreateCheckoutResDto(BaseModel):
    link: str
