import logging
from typing import Any
from datetime import datetime, timezone

from app.domain.entities import Transaction
from app.domain.repositories import ITransactionRepository, IWalletRepository
from app.domain.ports import IEventBus
from app.domain.events import WalletFundedEvent


logger = logging.getLogger("[ProcessDueSettlementsUseCase]")


class ProcessDueSettlementsUseCase:

    def __init__(
        self,
        txn_repo: ITransactionRepository,
        wallet_repo: IWalletRepository,
        event_bus: IEventBus,
    ):
        self.txn_repo = txn_repo
        self.wallet_repo = wallet_repo
        self.event_bus = event_bus

    async def execute(self, session: Any | None = None):
        if session is not None:
            self.txn_repo.set_session(session)
            self.wallet_repo.set_session(session)

        now = datetime.now(timezone.utc)
        due_transactions = await self.txn_repo.find_due_scheduled(now)

        logger.debug(f"Found {len(due_transactions)} due transaction(s)")

        for txn in due_transactions:
            await self._fund_account_from_txn(
                txn,
                self.txn_repo,
                self.wallet_repo,
                self.event_bus,
            )

    async def _fund_account_from_txn(
        self,
        txn: "Transaction",
        txn_repo: ITransactionRepository,
        wallet_repo: IWalletRepository,
        event_bus: IEventBus,
    ):
        now = datetime.now(timezone.utc)

        if (
            txn.settlement_status == "scheduled"
            and txn.delayed_settlement_until
            and now < txn.delayed_settlement_until
        ):
            logger.debug(
                f"Cannot complete a scheduled settlement early REf: {txn.reference}"
            )
            return

        logger.debug(f"Transaction: {txn.reference}: Fund wallet")

        wallet = await wallet_repo.get_by_user_or_create(
            txn.user_id,
            lock_for_update=True,
        )
        txn.settlement_status = "pending"
        wallet.deposit(txn.amount)
        await wallet_repo.save(wallet)
        await txn_repo.save(txn)

        ev = WalletFundedEvent.create(txn)
        await event_bus.publish(ev)
