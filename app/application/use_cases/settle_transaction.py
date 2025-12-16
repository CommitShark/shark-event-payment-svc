import asyncio
import logging
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from typing import Any

from app.config import settings
from app.domain.entities import Transaction
from app.domain.entities.value_objects import SettlementData
from app.domain.repositories import ITransactionRepository
from app.domain.ports import ITicketService, IUserService, IEventBus
from app.shared.errors import AppError

logger = logging.getLogger(__name__)

REFERRAL_PERCENTAGE = Decimal("12")


class SettleTicketPurchaseUseCase:
    def __init__(
        self,
        txn_repo: ITransactionRepository,
        ticket_service: ITicketService,
        user_service: IUserService,
        event_bus: IEventBus,
    ) -> None:
        self._txn_repo = txn_repo
        self._ticket_service = ticket_service
        self._user_service = user_service
        self._event_bus = event_bus

    async def execute(self, txn: Transaction, session: Any | None = None):
        if session is not None:
            self._txn_repo.set_session(session)

        # Validate charge data exists
        if not txn.charge_data:
            raise AppError(f"Transaction {txn.reference} missing charge data", 400)

        # Close Reservation
        logger.debug(f"Transaction {txn.reference}: Mark reservation as paid")
        await self._ticket_service.mark_reservation_as_paid(
            str(txn.reference),
            txn.amount,
        )
        logger.debug(f"Transaction {txn.reference}: Marked reservation as paid")

        logger.debug(f"Settle ticket purchase for txn with ref {txn.reference}")

        slug = txn.metadata.get("slug", None) if txn.metadata else None

        if not slug:
            logger.error(f"Slug not found for transaction with ref {txn.reference}")
            raise AppError(
                f"Transaction {txn.reference} missing event slug metadata", 400
            )

        logger.debug(f"Transaction {txn.reference}: Get organizer with slug: {slug}")
        organizer = await self._user_service.get_event_organizer(slug=slug)
        logger.debug("Organizer: %s", organizer)

        (
            system,
            organizer_referrer,
            buyer_referrer,
        ) = await asyncio.gather(
            self._user_service.get_system_user_id(),
            self._user_service.get_referral_info(organizer),  # organizer referrer
            self._user_service.get_referral_info(str(txn.user_id)),  # buyer referrer
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
                f"Invalid amount in transaction {txn.reference}: {e}",
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

        run_at = None
        if settings.settlement_delay_hours > 0:
            run_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.settlement_delay_hours
            )

        settlement_transactions = txn.create_settlement_transactions(run_at)

        if settings.settlement_delay_hours > 0:
            txn.settlement_status = "completed"
        else:
            txn.complete_settlement()

        # Persist the updated transaction
        await self._txn_repo.save(txn)
        for s_txn in settlement_transactions:
            await self._txn_repo.save(s_txn)

        for ev in txn.events:
            await self._event_bus.publish(ev)

        for s_txn in settlement_transactions:
            for s_ev in s_txn.events:
                await self._event_bus.publish(s_ev)

        logger.info(
            f"Transaction {txn.reference} processed successfully. "
            f"Created {len(txn.settlement_data)} settlements."
        )
