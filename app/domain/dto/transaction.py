from pydantic import BaseModel
from typing import Optional
from ..entities.value_objects import TransactionSettlementStatus, TransactionType


class TransactionFilter(BaseModel):
    status: Optional[TransactionSettlementStatus] = None
    type: Optional[TransactionType] = None
