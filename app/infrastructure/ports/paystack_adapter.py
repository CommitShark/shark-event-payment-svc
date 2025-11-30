import json
from decimal import Decimal
from pydantic import BaseModel
from app.domain.ports import IPaymentAdapter
from app.shared.errors import AppError
from app.utils.external_api_client import ExternalAPIClient


class BaseResDto(BaseModel):
    status: bool


class InitiateTransactionResDataDto(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class InitiateTransactionResDto(BaseResDto):
    data: InitiateTransactionResDataDto


class VerifyTransactionResDataDto(BaseModel):
    status: str
    reference: str
    amount: str
    paid_at: str
    created_at: str
    channel: str
    currency: str
    metadata: str | None = None
    fees: Decimal


class VerifyTransactionResDto(BaseResDto):
    status: bool
    data: VerifyTransactionResDataDto


class PaystackAdapter(IPaymentAdapter):
    def __init__(
        self,
        client: ExternalAPIClient,
    ) -> None:
        self._client = client

    async def is_transaction_complete(self, reference: str) -> bool:
        response = await self._client._get(endpoint=f"/transaction/verify/{reference}")

        try:
            parsed_res = VerifyTransactionResDto(**response)
        except Exception:
            raise AppError("Could not process payment, try again later", 500)

        return parsed_res.status and parsed_res.data.status == "success"

    async def create_checkout_link(
        self,
        email: str,
        amount: Decimal,
        callback_url: str,
        reference: str,
        metadata: dict | None = None,
    ) -> str:
        payload = {
            "email": email,
            "amount": str(amount * 100),
            "reference": reference,
            "callback_url": callback_url,
        }

        if metadata:
            payload["metadata"] = json.dumps(metadata)

        response = await self._client.post(
            endpoint="/transaction/initialize", data=payload
        )

        try:
            parsed_res = InitiateTransactionResDto(**response)
        except Exception:
            raise AppError("Could not process payment, try again later", 500)

        if not parsed_res.status:
            raise AppError("Could not process payment, try again later", 500)

        return parsed_res.data.authorization_url
