from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional

from app.domain.entities.value_objects import (
    TransactionDirection,
    TransactionSettlementStatus,
    BankDetails,
)
from .base import PaginatedReqDto, PaginatedResponseDto


class UpdateTransactionPinRequestDto(BaseModel):
    pin: str
    old_pin: Optional[str] = None


class BalanceDto(BaseModel):
    available: Decimal
    pending: Decimal
    has_pin: bool
    bank_details: Optional[BankDetails]


class TransactionDto(BaseModel):
    id: UUID
    amount: Decimal
    date: datetime
    description: str
    reference: str
    source: str
    settlement_status: TransactionSettlementStatus
    direction: TransactionDirection


class ListUserTransactionRequestDto(PaginatedReqDto):
    user_id: UUID


class ListUserTransactionResponseDto(PaginatedResponseDto[TransactionDto]):
    pass
