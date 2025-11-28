import click
import asyncio
import sys
import traceback

from typing import List, cast
from datetime import datetime, timezone
from pydantic import BaseModel

from app.domain.entities import ChargeSetting, ChargeSettingVersion, PriceRangeTier
from app.infrastructure.sqlalchemy.session import get_async_session

from ..factory import (
    get_charge_setting_repo,
    get_charge_setting_version_repo,
)
from ..utils import load_json_model


class Version(BaseModel):
    version_number: int
    tiers: list[PriceRangeTier]
    created_by: str
    change_reason: str


class Charge(BaseModel):
    name: str
    charge_type: str
    init_version: Version


@click.command("seed:charges")
def seed_charges():
    """Seed charges"""

    async def run():
        path = "./data/seed_charges.json"

        click.echo(click.style("🚀 Starting charge seed operation...", fg="cyan"))

        charges = load_json_model(path, Charge)

        if not charges or isinstance(charges, list) == False:
            click.echo(click.style(f"No charges found in {path}", fg="yellow"))
            return

        charges = cast(List[Charge], charges)

        click.echo(click.style(f"Loaded {len(charges)} charges"))

        async with get_async_session() as session:
            try:
                charge_repo = get_charge_setting_repo(session)
                charge_version_repo = get_charge_setting_version_repo(session)

                existing = await charge_repo.list_all()

                if len(existing) > 0:
                    click.echo(
                        click.style(
                            "Charge settings table is not empty. Seed aborted",
                            fg="yellow",
                        )
                    )
                    return

                for charge in charges:
                    model = ChargeSetting(
                        name=charge.name,
                        charge_type=charge.charge_type,
                    )

                    charge_repo.save(model)
                    await session.flush()

                    version = ChargeSettingVersion(
                        version_number=charge.init_version.version_number,
                        charge_setting_id=model.charge_setting_id,
                        change_reason=charge.init_version.change_reason,
                        created_by=charge.init_version.created_by,
                        tiers=charge.init_version.tiers,
                        effective_from=datetime.now(timezone.utc),
                    )

                    charge_version_repo.save(version)

            except Exception:
                click.echo(click.style("💥 Error seeding charges:", fg="red"))
                traceback.print_exc()
                sys.exit(1)

    asyncio.run(run())
