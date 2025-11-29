from typing import Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.domain.repositories import (
    IChargeSettingVersionRepository,
    IChargeSettingRepository,
)


class ChargeCalculationService:
    """
    Domain service for calculating charges.
    Coordinates between repositories and entities.
    """

    def __init__(
        self,
        charge_setting_repo: IChargeSettingRepository,
        version_repo: IChargeSettingVersionRepository,
    ):
        self.charge_setting_repo = charge_setting_repo
        self.version_repo = version_repo

    async def calculate_charge(
        self,
        charge_setting_id: UUID,
        base_amount: Decimal,
        at_time: Optional[datetime] = None,
    ) -> Optional[Decimal]:
        """
        Calculate charge for a base amount.

        Args:
            charge_setting_id: ID of the charge setting to use
            base_amount: The ticket price or base amount
            at_time: Time to use for version lookup (defaults to now)

        Returns:
            Calculated charge or None if no active version found
        """
        # Get appropriate version
        if at_time:
            version = await self.version_repo.get_version_at(charge_setting_id, at_time)
        else:
            version = await self.version_repo.get_current_version(charge_setting_id)

        if version is None:
            return None

        return version.calculate_charge(base_amount)

    async def get_charge_breakdown(
        self,
        charge_setting_id: UUID,
        base_amount: Decimal,
        at_time: Optional[datetime] = None,
    ) -> Optional[dict]:
        """
        Get detailed breakdown of charge calculation including which tier was used.

        Returns:
            Dictionary with tier info and calculated charge
        """
        # Get appropriate version
        if at_time:
            version = await self.version_repo.get_version_at(charge_setting_id, at_time)
        else:
            version = await self.version_repo.get_current_version(charge_setting_id)

        if version is None:
            return None

        tier = version.find_tier(base_amount)

        if tier is None:
            return None

        charge = tier.calculate_charge(base_amount)

        return {
            "base_amount": str(base_amount),
            "charge_setting_id": str(charge_setting_id),
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "tier_name": tier.tier_name,
            "tier_range": f"{tier.min_price} - {tier.max_price or 'unlimited'}",
            "percentage_rate": str(tier.percentage_rate),
            "calculated_charge": str(charge),
            "min_cap_applied": tier.min_charge is not None
            and charge == tier.min_charge,
            "max_cap_applied": tier.max_charge is not None
            and charge == tier.max_charge,
        }
