from app.domain.ports import IPaymentAdapter
from app.utils.signing import sign_payload
from app.config import settings


class ResolvePersonalAccountUseCase:
    def __init__(
        self,
        payment_adapter: IPaymentAdapter,
    ) -> None:
        self._payment_adapter = payment_adapter

    async def execute(self, account_number: str, bank_code: str):
        account = await self._payment_adapter.resolve_personal_bank(
            bank_code,
            account_number,
        )

        signature = sign_payload(account.model_dump(), settings.account_validation_key)

        return account, signature
