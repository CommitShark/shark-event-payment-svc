import logging
import asyncio
from uuid import UUID
from typing import cast
from decimal import Decimal, ROUND_HALF_UP

from app.domain.repositories import ITransactionRepository
from app.domain.ports import ITicketService, IUserService, IEventBus
from app.domain.entities import SettlementData, Transaction
from app.domain.events import TransactionCreatedEvent, TransactionCreatedPayload
from app.domain.events.base import DomainEvent
from app.shared.errors import AppError

from .base import IEventHandler
from .di import get_ticket_service, txn_repo_context, get_user_service, get_event_bus

logger = logging.getLogger(__name__)

REFERRAL_PERCENTAGE = Decimal("20")


class TransactionEventHandler(IEventHandler):
    events = [TransactionCreatedEvent]

    async def handle(self, event: DomainEvent):
        if isinstance(event, TransactionCreatedEvent):
            await self._process_transaction_created(event)
        else:
            logger.warning(f"Unhandled event type: {type(event).__name__}")

    async def _process_transaction_created(self, event: TransactionCreatedEvent):
        logger.debug(f"Processing transaction created AGG ID: {event.aggregate_id}")

        ticket_service = get_ticket_service()
        user_service = get_user_service()
        event_bus = get_event_bus()
        payload = cast(TransactionCreatedPayload, event.payload)

        async with txn_repo_context() as txn_repo:
            # Fetch transaction with row lock to prevent race conditions
            txn = await txn_repo.get_by_reference_or_none(
                UUID(payload.reference),
                lock_for_update=True,
            )

            if not txn:
                raise AppError(f"Transaction {payload.reference} not found", 404)

            if txn.transaction_type == "purchase" and txn.resource == "ticket":
                await self._settle_ticket_purchase_txn(
                    txn_repo=txn_repo,
                    ticket_service=ticket_service,
                    user_service=user_service,
                    payload=payload,
                    txn=txn,
                    event_bus=event_bus,
                )
            elif txn.transaction_type == "sale" or txn.transaction_type == "commission":
                # update users balance
                return
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

        # Validate charge data exists
        if not txn.charge_data:
            raise AppError(f"Transaction {payload.reference} missing charge data", 400)

        # Close Reservation
        await ticket_service.mark_reservation_as_paid(payload.reference)

        slug = txn.metadata.get("slug", None) if txn.metadata else None

        if not slug:
            raise AppError(
                f"Transaction {payload.reference} missing event slug metadata", 400
            )

        organizer = await user_service.get_event_organizer(slug=slug)

        (
            system,
            organizer_referee,
            buyer_referee,
        ) = await asyncio.gather(
            user_service.get_system_user_id(),
            user_service.get_referral_info(organizer),  # organizer referee
            user_service.get_referral_info(str(txn.user_id)),  # buyer referee
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
            )
        )

        # Handle referral commissions if applicable
        if buyer_referee or organizer_referee:
            # Calculate referral share
            referral_share = ((fee * REFERRAL_PERCENTAGE) / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Reduce platform fee by referral amount
            fee = fee - referral_share

            if buyer_referee and organizer_referee:
                # Split referral commission between both referees
                half_share = (referral_share / 2).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                txn.add_settlement(
                    SettlementData(
                        amount=half_share,
                        recipient_user=UUID(buyer_referee),
                        transaction_type="commission",
                    )
                )
                txn.add_settlement(
                    SettlementData(
                        amount=half_share,
                        recipient_user=UUID(organizer_referee),
                        transaction_type="commission",
                    )
                )
            elif buyer_referee:
                # Full referral commission to buyer's referee
                txn.add_settlement(
                    SettlementData(
                        amount=referral_share,
                        recipient_user=UUID(buyer_referee),
                        transaction_type="commission",
                    )
                )
            else:  # organizer_referee only
                # Full referral commission to organizer's referee
                txn.add_settlement(
                    SettlementData(
                        amount=referral_share,
                        recipient_user=UUID(organizer_referee),
                        transaction_type="commission",
                    )
                )

        # Platform fee settlement
        txn.add_settlement(
            SettlementData(
                amount=fee,
                recipient_user=UUID(system),
                transaction_type="commission",
            )
        )

        settlement_transactions = txn.create_settlement_transactions()

        txn.settlement_status = "completed"

        # Persist the updated transaction
        txn_repo.save(txn)
        for s_txn in settlement_transactions:
            txn_repo.save(s_txn)

        for ev in txn.events:
            await event_bus.publish(ev)

        for s_txn in settlement_transactions:
            for s_ev in s_txn.events:
                await event_bus.publish(s_ev)

        logger.info(
            f"Transaction {payload.reference} processed successfully. "
            f"Created {len(txn.settlement_data)} settlements."
        )
