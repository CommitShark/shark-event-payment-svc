import json
import logging
import traceback

from decimal import Decimal
from pydantic import BaseModel, ValidationError
from datetime import datetime
from uuid import UUID
from typing import TypeVar, Generic

from app.config import settings, paystack_config
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


class RequestWithdrawResDto(BaseModel):
    status: str


class CreateRecipientResDto(BaseModel):
    active: bool
    is_deleted: bool
    recipient_code: str


class PaystackAdapter(IPaymentAdapter):
    def __init__(
        self,
        client: ExternalAPIClient,
    ) -> None:
        self._client = client

    async def add_recipient(
        self,
        account_number: str,
        account_name: str,
        bank_code: str,
    ) -> str:
        payload = {
            "type": "nuban",
            "name": account_name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN",
        }

        response = await self._client.post(
            endpoint="/transferrecipient",
            data=payload,
        )

        try:
            parsed_res = BaseResWithDataDto[CreateRecipientResDto](**response)
        except ValidationError as e:
            print(
                "Pydantic validation error while parsing CreateRecipientResDto: %s",
                e.json(),
            )
            raise AppError(
                "Could not add recipient, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )
        except Exception as e:
            logger.error(
                "Unexpected error while parsing BaseResWithDataDto[CreateRecipientResDto]\nError: %s\nTraceback:\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise AppError(
                "Could not add recipient, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )

        if parsed_res.data.active and not parsed_res.data.is_deleted:
            logger.error(
                f"Invalid data Active={parsed_res.data.active}, IsDeleted={parsed_res.data.is_deleted}"
            )
            raise AppError(
                "Could not add recipient, try again later",
                500,
            )

        return parsed_res.data.recipient_code

    async def withdraw(
        self,
        amount: Decimal,
        recipient_id: str,
        ref: str,
        reason: str,
    ):
        payload = {
            "source": "balance",
            "amount": str(amount * 100),
            "recipient": recipient_id,
            "reference": ref,
            "reason": reason,
        }

        response = await self._client.post(
            endpoint="/transfer",
            data=payload,
        )

        try:
            parsed_res = BaseResWithDataDto[RequestWithdrawResDto](**response)
        except ValidationError as e:
            print(
                "Pydantic validation error while parsing RequestWithdrawResDto: %s",
                e.json(),
            )
            raise AppError(
                "Could not process withdrawal, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )
        except Exception as e:
            logger.error(
                "Unexpected error while parsing BaseResWithDataDto[RequestWithdrawResDto]\nError: %s\nTraceback:\n%s",
                str(e),
                traceback.format_exc(),
            )
            raise AppError(
                "Could not process withdrawal, try again later",
                500,
                error_code=ErrorCodes.DATA_VALIDATION_ERROR,
            )

        if not parsed_res.status:
            raise AppError("Could not process payment, try again later", 500)

        if (
            parsed_res.data.status != "pending"
            and parsed_res.data.status != "otp"
            and parsed_res.data.status != "success"
        ):
            logger.info(f"Unexpected status: {parsed_res.data.status}")
            raise AppError("Could not process payment, try again later", 500)

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


_adapter: PaystackAdapter | None = None


def get_PaystackAdapter():
    global _adapter
    if _adapter is None:
        print("Initialize Paystack Adapter")
        client = ExternalAPIClient(
            base_url=paystack_config.url,
            headers={
                "Authorization": f"Bearer {paystack_config.secret_key}",
            },
        )
        _adapter = PaystackAdapter(client)
    return _adapter


async def dispose_PaystackAdapter():
    print("Disposing Paystack Adapter")
    global _adapter
    if _adapter is not None:
        await _adapter._client.close()
