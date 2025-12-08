import click
import asyncio
from uuid import UUID

from app.application.dto.wallet import UpdateTransactionStatusReqDto
from app.domain.entities.value_objects import TransactionSettlementStatus
from ..factory import session_context, transaction_status_update_use_case


@click.command()
@click.option(
    "--id",
    prompt=False,
    type=UUID,
    help="Transaction ID to change",
)
@click.option(
    "--reason",
    prompt=False,
    type=str,
    help="Reason why the status is being changed",
)
@click.option(
    "--status",
    prompt=False,
    type=click.Choice(["failed", "completed"]),
    help="New Transaction status",
)
def update_transaction_status(
    id: UUID,
    reason: str,
    status: TransactionSettlementStatus,
):
    async def _run():
        async with transaction_status_update_use_case() as use_case:
            req = UpdateTransactionStatusReqDto(
                id=id,
                reason=reason,
                status=status,
            )

            await use_case.execute(req)
            click.echo("✅ Update successful.")

    asyncio.run(_run())
