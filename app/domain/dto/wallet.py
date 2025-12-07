from pydantic import BaseModel
from decimal import Decimal
from uuid import UUID
from datetime import datetime


class ExternalTransaction(BaseModel):
    amount: Decimal
    fees: Decimal
    reference: UUID
    occurred_on: datetime
    currency: str
    metadata: dict | None = None


class PersonalAccount(BaseModel):
    bank_code: str
    bank_name: str
    account_number: str
    account_name: str


class PersonalAccountWithSignature(PersonalAccount):
    signature: str


class BankItem(BaseModel):
    name: str
    code: str
