from uuid import UUID
from typing import Optional
from app.domain.repositories import IWalletRepository


class SetTransactionPinUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
    ) -> None:
        self._wallet_repo = wallet_repo

    async def execute(
        self,
        user_id: UUID,
        pin: str,
        old_pin: Optional[str] = None,
    ):
        wallet = await self._wallet_repo.get_by_user_or_create(user_id)

        if old_pin:
            wallet.change_pin(new_pin=pin, old_pin=old_pin)
        else:
            wallet.set_pin(pin)

        await self._wallet_repo.save(wallet)

        # TODO: Send user a notification letting them know their transaction pin was changed
