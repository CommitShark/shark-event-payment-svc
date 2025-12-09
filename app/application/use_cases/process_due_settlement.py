import logging
from typing import TYPE_CHECKING, Any
from datetime import datetime, timezone

from app.domain.repositories import ITransactionRepository

if TYPE_CHECKING:
    from .settle_transaction import SettleTicketPurchaseUseCase


logger = logging.getLogger("[ProcessDueSettlementsUseCase]")


class ProcessDueSettlementsUseCase:
    def __init__(
        self,
        txn_repo: ITransactionRepository,
        settle_use_case: "SettleTicketPurchaseUseCase",
    ):
        self.txn_repo = txn_repo
        self.settle_use_case = settle_use_case

    async def execute(self, session: Any | None = None):
        if session is not None:
            self.txn_repo.set_session(session)

        now = datetime.now(timezone.utc)
        due_transactions = await self.txn_repo.find_due_scheduled(now)

        logger.debug(f"Found {len(due_transactions)} due transaction(s)")

        for txn in due_transactions:
            await self.settle_use_case.execute(txn, session)
