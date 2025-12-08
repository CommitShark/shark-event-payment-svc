import logging
import asyncio
from uuid import UUID
from typing import cast
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.domain.repositories import ITransactionRepository, IWalletRepository
from app.domain.ports import ITicketService, IUserService, IEventBus
from app.domain.entities import Transaction
from app.domain.entities.value_objects import SettlementData
from app.domain.events import (
    TransactionCreatedEvent,
    TransactionCreatedPayload,
    WalletFundedEvent,
    CompleteWithdrawEvent,
    NotifyEvent,
)
from app.domain.events.base import DomainEvent
from app.shared.errors import AppError

from .base import IEventHandler
from .di import (
    get_ticket_service,
    session_context,
    get_user_service,
    get_event_bus,
    get_txn_repo,
    get_wallet_repo,
    get_IPaymentAdapter,
)

logger = logging.getLogger(__name__)

REFERRAL_PERCENTAGE = Decimal("12")


class TransactionEventHandler(IEventHandler):
    events = [
        TransactionCreatedEvent,
        CompleteWithdrawEvent,
    ]

    async def handle(self, event: DomainEvent):
        if isinstance(event, TransactionCreatedEvent):
            await self._process_transaction_created(event)
        elif isinstance(event, CompleteWithdrawEvent):
            await self._process_withdrawal_completion(event)
        else:
            logger.warning(f"Unhandled event type: {type(event).__name__}")

    async def _process_withdrawal_completion(self, ev: CompleteWithdrawEvent):
        logger.debug(f"Processing withdrawal completion AGG ID: {ev.aggregate_id}")

        async with session_context() as session:
            txn_repo = get_txn_repo(session)
            event_bus = get_event_bus()

            payload = ev.payload

            txn = await txn_repo.get_by_reference_or_none(UUID(payload.ref))

            if not txn:
                raise AppError(f"Transaction {payload.ref} not found", 404)

            logger.debug(f"Transaction with ref {payload.ref} found")

            if txn.settlement_status != "pending":
                logger.debug(
                    f"Transaction with ref {payload.ref} is no longer pending, status is {txn.settlement_status}",
                )
                return

            if txn.transaction_type != "withdrawal":
                raise AppError(
                    f"Transaction {payload.ref} is not a withdrawal it is a {txn.transaction_type}",
                    400,
                )

            if txn.amount != payload.amount:
                raise AppError(
                    f"Transaction {payload.ref} is valid \nAmount mismatch Provider {payload.amount} Txn {txn.amount}",
                    400,
                )

            txn.metadata = txn.metadata or {}
            txn.metadata["dest"] = payload.dest
            txn.metadata["completed_at"] = payload.date

            txn.complete_settlement()
            await txn_repo.save(txn)
            await session.commit()

            for t_ev in txn.events:
                await event_bus.publish(t_ev)

    async def _process_transaction_created(self, event: TransactionCreatedEvent):
        logger.debug(f"Processing transaction created AGG ID: {event.aggregate_id}")

        ticket_service = get_ticket_service()
        user_service = get_user_service()
        event_bus = get_event_bus()
        payload = cast(TransactionCreatedPayload, event.payload)

        async with session_context() as session:
            txn_repo = get_txn_repo(session)
            wallet_repo = get_wallet_repo(session)
            # Fetch transaction with row lock to prevent race conditions
            txn = await txn_repo.get_by_reference_or_none(
                UUID(payload.reference),
                lock_for_update=True,
            )

            if not txn:
                raise AppError(f"Transaction {payload.reference} not found", 404)

            logger.debug(f"Transaction with ref {payload.reference} found")

            if txn.settlement_status != "pending":
                logger.debug(
                    f"Transaction with ref {payload.reference} is no longer pending, status is {txn.settlement_status}",
                )
                return

            if txn.transaction_type == "purchase":
                if txn.resource == "ticket":
                    await self._settle_ticket_purchase_txn(
                        txn_repo=txn_repo,
                        ticket_service=ticket_service,
                        user_service=user_service,
                        payload=payload,
                        txn=txn,
                        event_bus=event_bus,
                    )
                else:
                    raise AppError(f"{txn} not implemented", 500)
            elif (
                txn.transaction_type == "sale"
                or txn.transaction_type == "commission"
                or txn.transaction_type == "wallet_funding"
            ):
                await self._fund_account_from_txn(
                    txn=txn,
                    txn_repo=txn_repo,
                    wallet_repo=wallet_repo,
                    event_bus=event_bus,
                )
            elif txn.transaction_type == "withdrawal":
                await self._transfer_to_external_bank(
                    txn,
                    txn_repo,
                    wallet_repo,
                    event_bus,
                )
            else:
                raise AppError(f"{txn} not implemented", 500)

    async def _settle_ticket_purchase_txn(
        self,
        txn: Transaction,
        txn_repo: ITransactionRepository,
        ticket_service: ITicketService,
        user_service: IUserService,
        payload: TransactionCreatedPayload,
        event_bus: IEventBus,
    ):
        if settings.settlement_delay_hours > 0:
            txn.settlement_status = "scheduled"
            txn.delayed_settlement_until = datetime.now(timezone.utc) + timedelta(
                hours=settings.settlement_delay_hours
            )

            await txn_repo.save(txn)

            logger.info(
                f"Transaction {payload.reference} scheduled for settlement at "
                f"{txn.delayed_settlement_until}"
            )

            return

        logger.debug(f"Settle ticket purchase for txn with ref {payload.reference}")

        # Validate charge data exists
        if not txn.charge_data:
            raise AppError(f"Transaction {payload.reference} missing charge data", 400)

        # Close Reservation
        logger.debug(f"Transaction {payload.reference}: Mark reservation as paid")
        await ticket_service.mark_reservation_as_paid(payload.reference)
        logger.debug(f"Transaction {payload.reference}: Marked reservation as paid")

        slug = txn.metadata.get("slug", None) if txn.metadata else None

        if not slug:
            logger.error(f"Slug not found for transaction with ref {payload.reference}")
            raise AppError(
                f"Transaction {payload.reference} missing event slug metadata", 400
            )

        logger.debug(
            f"Transaction {payload.reference}: Get organizer with slug: {slug}"
        )
        organizer = await user_service.get_event_organizer(slug=slug)
        logger.debug("Organizer: %s", organizer)

        (
            system,
            organizer_referrer,
            buyer_referrer,
        ) = await asyncio.gather(
            user_service.get_system_user_id(),
            user_service.get_referral_info(organizer),  # organizer referrer
            user_service.get_referral_info(str(txn.user_id)),  # buyer referrer
        )

        logger.debug(
            "Organizer: %s \nSystem: %s \nBuyer Referrer: %s \nOrganizer Referrer %s",
            organizer,
            system,
            buyer_referrer,
            organizer_referrer,
        )

        # Convert to Decimal with proper handling
        try:
            fee = Decimal(str(txn.charge_data.charge_amount))
            amount_paid = Decimal(str(txn.amount))
        except (ValueError, TypeError) as e:
            raise AppError(
                f"Invalid amount in transaction {payload.reference}: {e}",
                400,
            )

        if txn.charge_data.sponsored:
            raise AppError("Sponsored charge is not yet implemented", 500)

        # Credit the event organizer (amount paid minus platform fee)
        txn.add_settlement(
            SettlementData(
                amount=amount_paid - fee,
                recipient_user=UUID(organizer),
                transaction_type="sale",
                role="organizer",
            )
        )

        # Handle referral commissions if applicable
        if buyer_referrer or organizer_referrer:
            # Calculate referral share
            referral_share = ((fee * REFERRAL_PERCENTAGE) / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Reduce platform fee by referral amount
            fee = fee - referral_share

            if buyer_referrer and organizer_referrer:
                # Split referral commission between both referees
                half_share = (referral_share / 2).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                txn.add_settlement(
                    SettlementData(
                        amount=half_share,
                        recipient_user=UUID(buyer_referrer),
                        transaction_type="commission",
                        role="referrer",
                    )
                )
                txn.add_settlement(
                    SettlementData(
                        amount=half_share,
                        recipient_user=UUID(organizer_referrer),
                        transaction_type="commission",
                        role="referrer",
                    )
                )
            elif buyer_referrer:
                # Full referral commission to buyer's referee
                txn.add_settlement(
                    SettlementData(
                        amount=referral_share,
                        recipient_user=UUID(buyer_referrer),
                        transaction_type="commission",
                        role="referrer",
                    )
                )
            else:  # organizer_referee only
                # Full referral commission to organizer's referee
                txn.add_settlement(
                    SettlementData(
                        amount=referral_share,
                        recipient_user=UUID(organizer_referrer),
                        transaction_type="commission",
                        role="referrer",
                    )
                )

        # Platform fee settlement
        txn.add_settlement(
            SettlementData(
                amount=fee,
                recipient_user=UUID(system),
                transaction_type="commission",
                role="system_admin",
            )
        )

        settlement_transactions = txn.create_settlement_transactions()

        txn.complete_settlement()

        # Persist the updated transaction
        await txn_repo.save(txn)
        for s_txn in settlement_transactions:
            await txn_repo.save(s_txn)

        for ev in txn.events:
            await event_bus.publish(ev)

        for s_txn in settlement_transactions:
            for s_ev in s_txn.events:
                await event_bus.publish(s_ev)

        logger.info(
            f"Transaction {payload.reference} processed successfully. "
            f"Created {len(txn.settlement_data)} settlements."
        )

    async def _transfer_to_external_bank(
        self,
        txn: Transaction,
        txn_repo: ITransactionRepository,
        wallet_repo: IWalletRepository,
        event_bus: IEventBus,
    ):
        wallet = await wallet_repo.get_by_user_or_create(txn.user_id)

        if wallet.bank_details is None:
            raise AppError("User is yet to configure external bank", 400)

        logger.debug(f"Transaction: {txn.reference}: Withdraw")

        if settings.auto_withdrawal_enabled == 0:
            # Alert admin & User
            txn.metadata = txn.metadata or {}
            txn.metadata["mode"] = "manual"
            txn.metadata["dest"] = wallet.bank_details.build_dest()
            await txn_repo.save(txn)
            for ev in NotifyEvent.manual_withdrawal_initiated(txn):
                await event_bus.publish(ev)

            logger.debug(f"Transaction: {txn.reference}: Alerted User & Admin")
            return

        payment_adapter = get_IPaymentAdapter()

        txn.settlement_status = "processing"

        # Send money to users bank
        recipient = await payment_adapter.add_recipient(
            account_number=wallet.bank_details.account_number,
            account_name=wallet.bank_details.account_name,
            bank_code=wallet.bank_details.bank_code,
        )
        logger.debug(f"Transaction: {txn.reference}: Recipient ID: {recipient}")

        await payment_adapter.withdraw(
            amount=txn.amount,
            recipient_id=recipient,
            ref=str(txn.reference),
            reason="Wallet withdrawal",
        )

        txn.metadata = txn.metadata or {}
        txn.metadata["recipient_id"] = recipient

        # Save data
        await txn_repo.save(txn)

    async def _fund_account_from_txn(
        self,
        txn: Transaction,
        txn_repo: ITransactionRepository,
        wallet_repo: IWalletRepository,
        event_bus: IEventBus,
    ):
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
