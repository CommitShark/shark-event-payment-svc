from uuid import UUID
from app.domain.repositories import IWalletRepository


class GetBalanceUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
    ) -> None:
        self._wallet_repo = wallet_repo

    async def execute(self, user_id: UUID):
        return await self._wallet_repo.get_by_user_or_create(user_id)
