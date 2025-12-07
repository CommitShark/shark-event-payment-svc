from app.domain.ports import IPaymentAdapter


class ListBanksUseCase:
    def __init__(self, adapter: IPaymentAdapter) -> None:
        self._adapter = adapter

    async def execute(self):
        return await self._adapter.list_banks()
