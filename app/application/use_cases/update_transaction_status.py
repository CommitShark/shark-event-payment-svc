import logging
from uuid import UUID
from datetime import datetime, timezone
from app.domain.ports.user_service import IUserService
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
        user_service: IUserService,
    ) -> None:
        self._wallet_repo = wallet_repo
        self._txn_repo = txn_repo
        self._event_bus = event_bus
        self._user_service = user_service

    async def execute(self, req: UpdateTransactionStatusReqDto):
        txn = await self._txn_repo.get_by_id(req.id, lock_for_update=True)
        wallet = await self._wallet_repo.get_by_user_or_create(
            txn.user_id,
            lock_for_update=True,
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
                print(f"Error: {err}")
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
            txn.metadata = metadata
            txn.complete_settlement()

            # Create a new transaction for the fee if applicable
            system_user_id = await self._user_service.get_system_user_id()
            fee_transaction = txn.create_fee_transaction(UUID(system_user_id))
            if fee_transaction:
                await self._txn_repo.save(fee_transaction)

            await self._txn_repo.save(txn)

            for t_ev in txn.events:
                await self._event_bus.publish(t_ev)

            if fee_transaction:
                for f_ev in fee_transaction.events:
                    await self._event_bus.publish(f_ev)

            return True

        # If the request doesn't match any allowed updates
        err_msg = "Failed to update transaction. Invalid status or type."
        logger.debug(err_msg)
        raise AppError(err_msg, 400, {"req": req.model_dump_json()})
