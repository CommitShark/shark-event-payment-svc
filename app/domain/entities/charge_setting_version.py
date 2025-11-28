from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4


# === Value Objects ===


class PriceRangeTier(BaseModel):
    """
    Value object representing a single pricing tier with a price range
    and corresponding charge rate.
    """

    tier_name: Optional[str] = Field(
        default=None,
        description="Optional name for this tier (e.g., 'Basic', 'Premium')",
    )
    min_price: Decimal = Field(
        ge=0, description="Minimum price for this tier (inclusive)"
    )
    max_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Maximum price for this tier (inclusive, None for unlimited)",
    )
    percentage_rate: Decimal = Field(
        gt=0,
        le=100,
        description="Percentage rate to apply for this tier",
    )
    min_charge: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Minimum charge amount for this tier (optional floor)",
    )
    max_charge: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Maximum charge amount for this tier (optional ceiling)",
    )

    @field_validator(
        "percentage_rate", "min_price", "max_price", "min_charge", "max_charge"
    )
    @classmethod
    def validate_decimal_precision(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure monetary values have max 2 decimal places"""
        if v is not None:
            exponent = int(v.as_tuple().exponent)
            if exponent < -2:
                raise ValueError("Maximum 2 decimal places allowed")
        return v

    @model_validator(mode="after")
    def validate_price_range(self):
        """Ensure min_price doesn't exceed max_price"""
        if self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot exceed max_price")
        return self

    @model_validator(mode="after")
    def validate_charge_caps(self):
        """Ensure min_charge doesn't exceed max_charge"""
        if (
            self.min_charge is not None
            and self.max_charge is not None
            and self.min_charge > self.max_charge
        ):
            raise ValueError("min_charge cannot exceed max_charge")
        return self

    def applies_to(self, amount: Decimal) -> bool:
        """Check if this tier applies to a given amount"""
        if amount < self.min_price:
            return False
        if self.max_price is not None and amount > self.max_price:
            return False
        return True

    def calculate_charge(self, base_amount: Decimal) -> Decimal:
        """
        Calculate the charge for a given base amount using this tier's rate.

        Args:
            base_amount: The ticket price or base amount to calculate charge on

        Returns:
            The calculated charge amount after applying percentage and caps
        """
        # Calculate percentage-based charge
        charge = (base_amount * self.percentage_rate / 100).quantize(Decimal("0.01"))

        # Apply minimum cap if specified
        if self.min_charge is not None and charge < self.min_charge:
            charge = self.min_charge

        # Apply maximum cap if specified
        if self.max_charge is not None and charge > self.max_charge:
            charge = self.max_charge

        return charge


class ChargeSettingVersion(BaseModel):
    """
    Entity representing a single version of charge settings with tiered pricing.
    This is a separate entity that can be loaded independently.
    """

    version_id: UUID = Field(default_factory=uuid4)
    version_number: int = Field(ge=1, description="Sequential version number")

    # Tiered pricing configuration
    tiers: list[PriceRangeTier] = Field(
        min_length=1,
        description="List of pricing tiers, should cover all price ranges",
    )

    # Metadata
    effective_from: datetime = Field(description="When this version becomes active")
    effective_until: Optional[datetime] = Field(
        default=None,
        description="When this version expires (None if current)",
    )
    created_at: datetime = Field(default_factory=lambda x: datetime.now(timezone.utc))
    created_by: str = Field(description="User or system that created this version")
    change_reason: Optional[str] = Field(
        default=None, description="Reason for creating this version"
    )
    charge_setting_id: UUID

    @model_validator(mode="after")
    def validate_tiers(self):
        """Ensure tiers don't overlap and are properly ordered"""
        if len(self.tiers) == 0:
            raise ValueError("At least one tier is required")

        # Sort tiers by min_price
        sorted_tiers = sorted(self.tiers, key=lambda t: t.min_price)

        # Check for gaps and overlaps
        for i in range(len(sorted_tiers)):
            current = sorted_tiers[i]

            # Check for overlaps with next tier
            if i < len(sorted_tiers) - 1:
                next_tier = sorted_tiers[i + 1]

                if current.max_price is None:
                    raise ValueError(
                        f"Tier starting at {current.min_price} has no max_price but is not the last tier"
                    )

                # Check for overlap
                if current.max_price >= next_tier.min_price:
                    raise ValueError(
                        f"Tiers overlap: {current.min_price}-{current.max_price} and "
                        f"{next_tier.min_price}-{next_tier.max_price}"
                    )

                # Check for gaps
                if current.max_price + Decimal("0.01") < next_tier.min_price:
                    raise ValueError(
                        f"Gap between tiers: {current.max_price} and {next_tier.min_price}"
                    )
            else:
                # Last tier should have no max_price (unlimited)
                if current.max_price is not None:
                    raise ValueError(
                        f"Last tier should have max_price=None for unlimited upper bound"
                    )

        # Update tiers to be sorted
        self.tiers = sorted_tiers

        return self

    @model_validator(mode="after")
    def validate_effective_dates(self):
        """Ensure effective_until is after effective_from"""
        if (
            self.effective_until is not None
            and self.effective_until <= self.effective_from
        ):
            raise ValueError("effective_until must be after effective_from")
        return self

    def find_tier(self, base_amount: Decimal) -> Optional[PriceRangeTier]:
        """Find the appropriate tier for a given amount"""
        for tier in self.tiers:
            if tier.applies_to(base_amount):
                return tier
        return None

    def calculate_charge(self, base_amount: Decimal) -> Decimal:
        """
        Calculate the charge for a given base amount using the appropriate tier.

        Args:
            base_amount: The ticket price or base amount to calculate charge on

        Returns:
            The calculated charge amount

        Raises:
            ValueError: If no tier applies to the given amount
        """
        if base_amount < 0:
            raise ValueError("base_amount must be non-negative")

        tier = self.find_tier(base_amount)

        if tier is None:
            raise ValueError(f"No tier found for amount: {base_amount}")

        return tier.calculate_charge(base_amount)

    def is_active(self, at_time: Optional[datetime] = None) -> bool:
        """Check if this version is active at a given time"""
        check_time = at_time or datetime.now(timezone.utc)

        if check_time < self.effective_from:
            return False

        if self.effective_until is not None and check_time >= self.effective_until:
            return False

        return True
