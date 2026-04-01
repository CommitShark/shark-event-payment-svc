from pydantic import BaseModel, EmailStr
from decimal import Decimal

from .charge_request import GetChargeResDto


class CheckoutChargeMetadata(BaseModel):
    base_amount: str
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    sponsored: bool
    user: str
    event_id: str
    occurrence_id: str


class TicketCheckoutChargeMetadata(CheckoutChargeMetadata):
    ticket_type_id: str
    quantity: int


class CheckoutMetaData(BaseModel):
    ticket_charge: TicketCheckoutChargeMetadata
    extras_charge: CheckoutChargeMetadata | None
    signature: str
    action: str


class DepositCheckoutMetaData(BaseModel):
    charge_setting_id: str
    version_id: str
    version_number: int
    calculated_charge: str
    sponsored: bool
    user: str
    signature: str
    action: str
    amount: str


class CreateCheckoutReqDto(BaseModel):
    charge: GetChargeResDto
    reservation_id: str
    ticket_type_id: str
    occurrence_id: str
    slug: str
    event_id: str
    email: EmailStr
    quantity: int


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
    amount: Decimal
