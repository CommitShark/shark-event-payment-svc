import click
import asyncio
from tabulate import tabulate

from app.utils.money_utils import format_currency
from app.application.dto.wallet import ListTransactionRequestDto
from app.domain.dto import TransactionFilter
from ..factory import session_context, get_ListTransactionUseCase


@click.command()
@click.option(
    "--pending",
    prompt=False,
    is_flag=True,
    help="Only pending transactions are returned",
)
@click.option(
    "--withdrawal",
    prompt=False,
    is_flag=True,
    help="Only withdrawal transactions are returned",
)
@click.option("--page", prompt=False, default=1, type=int)
def list_transactions(page: int, pending: bool, withdrawal: bool):

    async def _run():
        async with session_context() as session:
            use_case = get_ListTransactionUseCase(session)

            filter = TransactionFilter()

            if pending:
                filter.status = "pending"

            if withdrawal:
                filter.type = "withdrawal"

            req = ListTransactionRequestDto(
                filter=filter,
                page=page,
                page_size=10,
            )

            result, total = await use_case.execute(req)

            if not result:
                click.echo(f"No transactions found for page {page}.")
                return

            # Summary line
            click.echo(
                f"\n📊 {total} Transactions found | Page {page} of {((total - 1) // 10) + 1}"
            )
            click.echo(f"📄 Showing {len(result)} transactions\n")

            # Prepare table data
            table_data = []
            for txn in result:
                # Format date nicely
                created_at = (
                    txn.created_at.strftime("%Y-%m-%d %H:%M")
                    if hasattr(txn.created_at, "strftime")
                    else txn.created_at
                )

                # Add status indicator
                status_icon = (
                    "⏳"
                    if txn.settlement_status == "pending"
                    else "✅" if txn.settlement_status == "completed" else "❌"
                )

                # Add type indicator
                type_icon = (
                    "⬇️"
                    if txn.transaction_type == "withdrawal"
                    else "⬆️" if txn.transaction_type == "deposit" else "🔄"
                )

                table_data.append(
                    [
                        txn.id,
                        f"{type_icon} {txn.transaction_type.title()}",
                        f"{status_icon} {txn.settlement_status.title()}",
                        txn.user_id,
                        created_at,
                        format_currency(txn.amount),
                    ]
                )

            # Display table
            headers = ["ID", "Type", "Status", "User ID", "Created At", "Amount"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

            total_amount = sum(t.amount for t in result)
            pending_count = sum(1 for t in result if t.settlement_status == "pending")
            withdrawal_count = sum(
                1 for t in result if t.transaction_type == "withdrawal"
            )
            deposit_count = len(result) - withdrawal_count

            click.echo(f"\n{'═' * 60}")
            click.echo("📊 PAGE SUMMARY:")
            click.echo(f"  • Total Amount: {format_currency(total_amount)}")
            click.echo(f"  • Transactions: {len(result)}")
            click.echo(f"  • Pending: {pending_count}")
            click.echo(f"  • Withdrawals: {withdrawal_count}")
            click.echo(f"  • Deposits: {deposit_count}")
            click.echo(f"{'═' * 60}")

    asyncio.run(_run())
