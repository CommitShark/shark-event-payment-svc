import click
import logging


from .commands import (
    seed_charges,
    list_transactions,
    update_transaction_status,
    verify_ticket_purchase,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@click.group()
def cli():
    """Shark Event CLI"""
    pass


cli.add_command(seed_charges)
cli.add_command(list_transactions, "view:transactions")
cli.add_command(update_transaction_status, "update:transaction:status")
cli.add_command(verify_ticket_purchase, "verify:ticket:purchase")

if __name__ == "__main__":
    cli()
