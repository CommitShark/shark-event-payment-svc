import click
import asyncio
from uuid import UUID

from app.application.use_cases import VerifyTicketPurchaseTransactionUseCase
from app.infrastructure.ports.paystack_adapter import get_PaystackAdapter
from app.infrastructure.ports.kafka_event_bus import kafka_event_bus
from ..factory import session_context, get_ITransactionRepository


@click.command()
@click.option(
    "--user",
    type=UUID,
    help="User Auth ID",
    required=True,
)
@click.option(
    "reference",
    type=UUID,
    help="Transaction Reference",
    required=True,
)
def verify_ticket_purchase(
    user: UUID,
    reference: UUID,
):
    async def _run():
        async with session_context() as session:
            payment_adapter = get_PaystackAdapter()

            await kafka_event_bus.connect()

            use_case = VerifyTicketPurchaseTransactionUseCase(
                payment_adapter=payment_adapter,
                event_bus=kafka_event_bus,
                txn_repo=get_ITransactionRepository(session),
            )

            await use_case.execute(reference=str(reference), user_id=user)
            click.echo("✅ Verified successfully.")

        asyncio.run(_run())
