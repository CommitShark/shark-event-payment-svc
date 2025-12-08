from app.domain.repositories import ITransactionRepository
from app.application.dto.wallet import (
    ListUserTransactionRequestDto,
    ListTransactionRequestDto,
    TransactionDto,
)
from app.application.dto.base import PaginatedResponseDto
from app.application.mappers.wallet import transaction_to_dto


class ListTransactionUseCase:
    def __init__(self, txn_repo: ITransactionRepository) -> None:
        self._txn_repo = txn_repo

    async def execute(self, req: ListTransactionRequestDto):
        return await self._txn_repo.query(
            offset=req.offset,
            limit=req.page_size,
            filter=req.filter,
        )

    async def by_user(
        self,
        req: ListUserTransactionRequestDto,
    ) -> PaginatedResponseDto[TransactionDto]:
        entities, total = await self._txn_repo.query_by_user(
            offset=req.offset,
            limit=req.page_size,
            user_id=req.user_id,
        )

        return PaginatedResponseDto.create(
            page=req.page,
            items=[transaction_to_dto(e) for e in entities],
            page_size=req.page_size,
            total=total,
        )
