import json
import logging
import traceback

from decimal import Decimal
from pydantic import BaseModel, ValidationError
from datetime import datetime
from uuid import UUID
from typing import TypeVar, Generic

from app.config import settings
from app.domain.ports import IPaymentAdapter
from app.shared.errors import AppError, ErrorCodes
from app.utils.external_api_client import ExternalAPIClient
from app.domain.dto import BankItem, ExternalTransaction, PersonalAccount


T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseResDto(BaseModel):
    status: bool


class BaseResWithDataDto(BaseModel, Generic[T]):
    status: bool
    data: T


class InitiateTransactionResDataDto(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class InitiateTransactionResDto(BaseResDto):
    data: InitiateTransactionResDataDto


class VerifyTransactionResDataDto(BaseModel):
    status: str
    reference: UUID
    amount: Decimal
    paid_at: datetime
    created_at: str
    channel: str
    currency: str
    metadata: dict | None = None
    fees: Decimal


class VerifyTransactionResDto(BaseResDto):
    status: bool
    data: VerifyTransactionResDataDto


class PaystackPersonalAccountResDto(BaseModel):
    account_number: str
    account_name: str


class PaystackAdapter(IPaymentAdapter):
    def __init__(
        self,
        client: ExternalAPIClient,
    ) -> None:
        self._client = client

    async def resolve_personal_bank(
        self,
        bank: str,
        account: str,
    ) -> PersonalAccount:
        response = await self._client._get(
            endpoint="/bank/resolve",
            params={
                "account_number": account,
                "bank_code": bank,
            },
        )

        try:
            parsed_res = BaseResWithDataDto[PaystackPersonalAccountResDto](**response)
        except ValidationError as e:
            print(
                "Pydantic validation error while parsing VerifyTransactionResDto: %s",
                e.json(),
            )
            raise AppError(
                "Could not process payment, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )
        except Exception as e:
            logger.error(
                "Unexpected error while parsing BaseResWithDataDto[PaystackPersonalAccountResDto]\nError: %s\nTraceback:\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise AppError(
                "Could not resolve account, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )

        banks = await self.list_banks()
        selected_bank = next((b for b in banks if b.code == bank), None)

        if not selected_bank:
            raise AppError("Bank could not be resolved.", 500)

        return PersonalAccount(
            account_name=parsed_res.data.account_name,
            account_number=parsed_res.data.account_number,
            bank_code=bank,
            bank_name=selected_bank.name,
        )

    async def get_valid_transaction(
        self,
        reference: str,
    ) -> ExternalTransaction:
        response = await self._client._get(
            endpoint=f"/transaction/verify/{reference}",
        )

        try:
            parsed_res = VerifyTransactionResDto(**response)
        except ValidationError as e:
            logger.error(
                "Pydantic validation error while parsing VerifyTransactionResDto: %s",
                e.json(),
            )
            raise AppError(
                "Could not process payment, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )
        except Exception as e:
            logger.error(
                "Unexpected error while parsing VerifyTransactionResDto\nError: %s\nTraceback:\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise AppError(
                "Could not process payment, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )

        if parsed_res.status and parsed_res.data.status == "success":
            return ExternalTransaction(
                amount=Decimal(parsed_res.data.amount) / 100,
                fees=parsed_res.data.fees,
                currency=parsed_res.data.currency,
                metadata=parsed_res.data.metadata,
                occurred_on=parsed_res.data.paid_at,
                reference=parsed_res.data.reference,
            )

        raise AppError("Invalid or unsuccessful transaction", 400)

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
            endpoint="/transaction/initialize",
            data=payload,
        )

        try:
            parsed_res = InitiateTransactionResDto(**response)
        except Exception:
            raise AppError("Could not process payment, try again later", 500)

        if not parsed_res.status:
            raise AppError("Could not process payment, try again later", 500)

        return parsed_res.data.authorization_url

    async def list_banks(self) -> list[BankItem]:
        response = await self._client._get(
            endpoint="/bank",
            params={
                "country": "nigeria",
                "perPage": 100,
            },
        )

        try:
            parsed_res = BaseResWithDataDto[list[BankItem]](**response)
        except Exception:
            raise AppError("Could not process banks list, try again later", 500)

        if not parsed_res.status:
            raise AppError("Could not process bank list, try again later", 500)

        result = parsed_res.data

        if settings.debug:
            result.append(
                BankItem(
                    code="001",
                    name="Test Bank",
                )
            )

        return result
