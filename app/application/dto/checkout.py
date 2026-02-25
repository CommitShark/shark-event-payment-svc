from pydantic import BaseModel, EmailStr
from decimal import Decimal


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


class DepositCheckoutMetaData(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    sponsored: bool
    user: str
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
    base_amount: Decimal


class PublicCreateCheckoutReqDto(CreateCheckoutReqDto):
    user_auth_id: str


class CreateAttendeeCheckoutReqDto(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    signature: str
    amount: Decimal


class CreateCheckoutResDto(BaseModel):
    link: str


class VerifyTicketPurchaseReqDto(BaseModel):
    reference: str


class PublicVerifyTicketPurchaseReqDto(VerifyTicketPurchaseReqDto):
    user_auth_id: str


class VerifyTicketPurchaseResDto(BaseModel):
    success: bool
