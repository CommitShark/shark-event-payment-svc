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
