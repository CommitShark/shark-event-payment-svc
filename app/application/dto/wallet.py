from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.entities.value_objects import (
    TransactionDirection,
    TransactionSettlementStatus,
)
from .base import PaginatedReqDto, PaginatedResponseDto


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
