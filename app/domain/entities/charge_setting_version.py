from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    field_serializer,
)
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from app.shared.errors import AppError


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
        ge=0,
        le=100,
        description="Percentage rate to apply for this tier",
    )
    additional_charge: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Additional charge after applying percentage charge",
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
        "percentage_rate",
        "min_price",
        "max_price",
        "min_charge",
        "max_charge",
        "additional_charge",
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

    @field_serializer("*", when_used="json")
    def serialize_decimal(self, v):
        if isinstance(v, Decimal):
            return format(v, "f")  # keeps exact decimal, no scientific notation
        return v

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
        charge = (
            (base_amount * self.percentage_rate / 100).quantize(Decimal("0.01"))
            if self.percentage_rate > 0
            else Decimal("0.00")
        )

        if self.additional_charge:
            charge += self.additional_charge

        # Apply minimum cap if specified
        if self.min_charge is not None and charge < self.min_charge:
            charge = self.min_charge

        # Apply maximum cap if specified
        if self.max_charge is not None and charge > self.max_charge:
            charge = self.max_charge

        return charge


class TierOverlapStrategy(str, Enum):
    """Strategy for handling overlapping tiers"""

    SUM = "sum"  # Sum charges from all applicable tiers
    HIGHEST = "highest"  # Use the highest charge
    LOWEST = "lowest"  # Use the lowest charge
    FIRST = "first"  # Use the first applicable tier (order matters)
    LAST = "last"  # Use the last applicable tier (order matters)


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

    allow_overlap: bool = Field(
        default=False,
        description="Whether tiers can overlap (multiple tiers can apply to the same price)",
    )

    overlap_strategy: Optional[TierOverlapStrategy] = Field(
        default=None,
        description="Strategy for handling overlapping tiers (required if allow_overlap=True)",
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
        """Validate tiers based on overlap setting"""
        if len(self.tiers) == 0:
            raise ValueError("At least one tier is required")

        # Sort tiers by min_price for consistent processing
        sorted_tiers = sorted(self.tiers, key=lambda t: t.min_price)

        if not self.allow_overlap:
            # Strict validation: no overlaps or gaps
            self._validate_no_overlaps(sorted_tiers)
        else:
            # Validate overlap strategy is specified
            if self.overlap_strategy is None:
                raise ValueError(
                    "overlap_strategy must be specified when allow_overlap=True"
                )

            # Validate based on strategy
            self._validate_with_overlaps(sorted_tiers)

        # Update tiers to be sorted
        self.tiers = sorted_tiers

        return self

    def _validate_with_overlaps(self, sorted_tiers: list[PriceRangeTier]):
        """Validate tiers when overlaps are allowed"""
        # For SUM strategy, ensure tiers are compatible
        if self.overlap_strategy == TierOverlapStrategy.SUM:
            # Check for circular dependencies or impossible combinations
            # (e.g., no additional validation needed for now)
            pass

    def _validate_no_overlaps(self, sorted_tiers: list[PriceRangeTier]):
        """Validate that tiers don't overlap and have no gaps"""
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

        if self.allow_overlap:
            raise AppError("Charge can have more than one tiers that match", 500)

        for tier in self.tiers:
            if tier.applies_to(base_amount):
                return tier

        return None

    def find_applicable_tiers(self, base_amount: Decimal) -> list[PriceRangeTier]:
        """Find all tiers that apply to a given amount"""
        applicable = []
        for tier in self.tiers:
            if tier.applies_to(base_amount):
                applicable.append(tier)
        return applicable

    def calculate_charge(self, base_amount: Decimal) -> Decimal:
        """
        Calculate the charge for a given base amount using the appropriate tier(s).

        Args:
            base_amount: The ticket price or base amount to calculate charge on

        Returns:
            The calculated charge amount

        Raises:
            ValueError: If no tier applies to the given amount or if overlapping
                       tiers are misconfigured
        """
        if base_amount < 0:
            raise ValueError("base_amount must be non-negative")

        applicable_tiers = self.find_applicable_tiers(base_amount)

        if not applicable_tiers:
            raise ValueError(f"No tier found for amount: {base_amount}")

        if len(applicable_tiers) == 1 or not self.allow_overlap:
            # Single tier case (or overlaps not allowed)
            return applicable_tiers[0].calculate_charge(base_amount)

        # Multiple tiers case with overlaps allowed
        return self._calculate_overlapping_charge(applicable_tiers, base_amount)

    def _calculate_overlapping_charge(
        self, applicable_tiers: list[PriceRangeTier], base_amount: Decimal
    ) -> Decimal:
        """Calculate charge when multiple tiers apply"""

        if self.overlap_strategy == TierOverlapStrategy.SUM:
            # Sum charges from all applicable tiers
            total = Decimal("0.00")
            for tier in applicable_tiers:
                total += tier.calculate_charge(base_amount)
            return total

        elif self.overlap_strategy == TierOverlapStrategy.HIGHEST:
            # Take the highest charge
            charges = [t.calculate_charge(base_amount) for t in applicable_tiers]
            return max(charges)

        elif self.overlap_strategy == TierOverlapStrategy.LOWEST:
            # Take the lowest charge
            charges = [t.calculate_charge(base_amount) for t in applicable_tiers]
            return min(charges)

        elif self.overlap_strategy == TierOverlapStrategy.FIRST:
            # Take the first applicable tier (based on min_price)
            applicable_tiers.sort(key=lambda t: t.min_price)
            return applicable_tiers[0].calculate_charge(base_amount)

        elif self.overlap_strategy == TierOverlapStrategy.LAST:
            # Take the last applicable tier (highest min_price)
            applicable_tiers.sort(key=lambda t: t.min_price, reverse=True)
            return applicable_tiers[0].calculate_charge(base_amount)

        else:
            raise ValueError(f"Unknown overlap strategy: {self.overlap_strategy}")

    def is_active(self, at_time: Optional[datetime] = None) -> bool:
        """Check if this version is active at a given time"""
        check_time = at_time or datetime.now(timezone.utc)

        if check_time < self.effective_from:
            return False

        if self.effective_until is not None and check_time >= self.effective_until:
            return False

        return True
