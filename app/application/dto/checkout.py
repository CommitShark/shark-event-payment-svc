from pydantic import BaseModel, EmailStr


class CheckoutMetaData(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    ticket_type_id: str
    slug: str
    sponsored: bool
    user: str
    quantity: int
    signature: str


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
    quantity: int


class CreateCheckoutResDto(BaseModel):
    link: str


class VerifyTicketPurchaseReqDto(BaseModel):
    reference: str


class VerifyTicketPurchaseResDto(BaseModel):
    success: bool
