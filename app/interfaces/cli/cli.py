import click
import logging


from .commands import seed_categories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@click.group()
def cli():
    """Shark Event CLI"""
    pass


cli.add_command(seed_categories)

if __name__ == "__main__":
    cli()
