import logging
from datetime import datetime, timezone
from app.domain.repositories import IWalletRepository, ITransactionRepository
from app.domain.ports import IEventBus
from app.application.dto.wallet import UpdateTransactionStatusReqDto
from app.shared.errors import AppError

logger = logging.getLogger(__name__)


class UpdateTransactionStatusUseCase:
    def __init__(
        self,
        wallet_repo: IWalletRepository,
        txn_repo: ITransactionRepository,
        event_bus: IEventBus,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._txn_repo = txn_repo
        self._event_bus = event_bus

    async def execute(self, req: UpdateTransactionStatusReqDto):
        txn = await self._txn_repo.get_by_id(req.id, lock_for_update=True)
        wallet = await self._wallet_repo.get_by_user_or_create(
            txn.user_id, lock_for_update=True
        )

        if (
            req.status == "failed"
            and txn.transaction_type == "withdrawal"
            and txn.settlement_status == "pending"
        ):
            metadata = txn.metadata or {}

            mode = metadata.get("mode")

            if mode != "manual":
                err = f"Invalid transaction mode {mode}"
                logger.debug(err)
                raise AppError(err, 400)

            refundable_amount = txn.mark_as_failed(req.reason)

            if refundable_amount:
                wallet.deposit(refundable_amount)

            await self._txn_repo.save(txn)
            await self._wallet_repo.save(wallet)

            for ev in txn.events:
                await self._event_bus.publish(ev)

            return True
        elif (
            req.status == "completed"
            and txn.transaction_type == "withdrawal"
            and txn.settlement_status == "pending"
        ):
            metadata = txn.metadata or {}

            mode = metadata.get("mode")

            if mode != "manual":
                err = f"Invalid transaction mode {mode}"
                logger.debug(err)
                raise AppError(err, 400)

            metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
            txn.complete_settlement()
            await self._txn_repo.save(txn)

            for t_ev in txn.events:
                await self._event_bus.publish(t_ev)

            return True

        # If the request doesn't match any allowed updates
        err_msg = "Failed to update transaction. Invalid status or type."
        logger.debug(err_msg)
        raise AppError(err_msg, 400, {"req": req.model_dump_json()})
