import asyncio
import logging
from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, timedelta
from typing import Any

from app.config import settings
from app.domain.entities import Transaction
from app.domain.entities.value_objects import SettlementData, SettlementDataResource
from app.domain.dto.extra import ExtraOrderDto
from app.domain.dto.event import EventOccurrence
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
        print(f"Fetch reservation extras")
        orders = await self._ticket_service.get_reservation_extra_orders(
            str(txn.reference)
        )

        print(f"Settle ticket purchase for txn with ref {txn.reference}")

        event = txn.metadata.get("event", None) if txn.metadata else None

        if not event:
            print(
                f"Event not found in metadata for transaction with ref {txn.reference}"
            )
            raise AppError(
                f"Transaction {txn.reference} missing event in metadata", 400
            )

        ticket_meta = txn.metadata.get("ticket", None) if txn.metadata else None
        ticket_quantity = int(ticket_meta.get("quantity", 1)) if ticket_meta else 1
        support_amount_raw = (
            ticket_meta.get("support", "0") or "0" if ticket_meta else "0"
        )
        support_amount = Decimal(support_amount_raw)

        print(f"Transaction {txn.reference}: Get organizer with slug: {str(event)}")
        organizer = await self._user_service.get_event_organizer(
            event_id=EventOccurrence.model_validate(event).id,
        )
        print("Organizer: %s", organizer)

        (
            system,
            organizer_referrer,
            buyer_referrer,
        ) = await asyncio.gather(
            self._user_service.get_system_user_id(),
            self._user_service.get_referral_info(organizer),  # organizer referrer
            self._user_service.get_referral_info(str(txn.user_id)),  # buyer referrer
        )

        print(
            "Organizer: %s \nSystem: %s \nBuyer Referrer: %s \nOrganizer Referrer %s",
            organizer,
            system,
            buyer_referrer,
            organizer_referrer,
        )

        # Convert to Decimal with proper handling
        try:
            ticket_fee = txn.get_total_charge_amount("tickets")
            extras_fee = txn.get_total_charge_amount("extras")
            amount_paid = txn.amount
        except (ValueError, TypeError) as e:
            raise AppError(
                f"Invalid amount in transaction {txn.reference}: {e}",
                400,
            )

        if txn.is_charge_sponsored("tickets"):
            raise AppError("Sponsored charge is not yet implemented", 500)

        has_extras = len(orders) > 0
        ticket_amount = amount_paid

        if has_extras:
            extras_total = ExtraOrderDto.calculate_total(orders)
            ticket_amount = ticket_amount - (extras_total + extras_fee + ticket_fee)
        else:
            ticket_amount = ticket_amount - ticket_fee

        cost_per_ticket = (ticket_amount + ticket_fee) / ticket_quantity

        print(f"Transaction {txn.reference}: Mark reservation as paid")
        await self._ticket_service.mark_reservation_as_paid(
            str(txn.reference),
            cost_per_ticket,
        )
        print(
            f"Transaction {txn.reference}: Marked reservation as paid. Found {len(orders)} extra orders"
        )

        # Credit the event organizer (amount paid minus platform fee)
        txn.add_settlement(
            SettlementData(
                amount=ticket_amount,
                recipient_user=UUID(organizer),
                transaction_type="sale",
                role="organizer",
            )
        )

        if has_extras:
            for o in orders:
                txn.add_settlement(
                    SettlementData(
                        amount=o.cost,
                        recipient_user=UUID(organizer),
                        transaction_type="sale",
                        role="organizer",
                        resource=SettlementDataResource(
                            resource="extra",
                            resource_id=o.extra_id,
                        ),
                        metadata={"extra_order": {**o.model_dump()}},
                    )
                )

        # Handle referral commissions if applicable
        if buyer_referrer or organizer_referrer:
            # Calculate referral share
            referral_share = (
                ((ticket_fee * REFERRAL_PERCENTAGE) / 100).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if ticket_fee > 0
                else Decimal(0)
            )

            # Reduce platform fee by referral amount
            ticket_fee = ticket_fee - referral_share if ticket_fee > 0 else Decimal(0)

            if referral_share > Decimal(0):
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
                amount=ticket_fee,
                recipient_user=UUID(system),
                transaction_type="commission",
                role="system_admin",
            )
        )

        if has_extras and extras_fee > Decimal(0):
            txn.add_settlement(
                SettlementData(
                    amount=extras_fee,
                    recipient_user=UUID(system),
                    transaction_type="commission",
                    role="system_admin",
                    resource=SettlementDataResource(resource="extras"),
                    metadata={"extra_orders": [o.model_dump() for o in orders]},
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

        print(
            f"Transaction {txn.reference} processed successfully. "
            f"Created {len(txn.settlement_data)} settlements."
        )
