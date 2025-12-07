from uuid import UUID

from app.utils.signing import sign_payload
from app.config import settings
from app.shared.errors import AppError
from app.domain.repositories import IWalletRepository
from app.application.dto.wallet import SaveBankReqDto


class SaveBankUseCase:
    def __init__(self, wallet_repo: IWalletRepository) -> None:
        self.wallet_repo = wallet_repo

    async def execute(self, req: SaveBankReqDto, user: UUID):
        req_dict = req.model_dump()

        sig = req_dict.pop("signature")
        pin = req_dict.pop("pin")

        expected_sig = sign_payload(req_dict, settings.account_validation_key)

        if sig != expected_sig:
            raise AppError("We could not validate your request. Please try again", 400)

        wallet = await self.wallet_repo.get_by_user_or_create(user)

        if not wallet.has_pin:
            raise AppError("Please setup your transaction pin before proceeding", 400)

        if not wallet.verify_pin(pin):
            raise AppError("Invalid pin", 400)

        wallet.set_bank_details(
            bank_code=req.bank_code,
            bank_name=req.bank_name,
            name=req.account_name,
            number=req.account_number,
        )

        await self.wallet_repo.save(wallet)
