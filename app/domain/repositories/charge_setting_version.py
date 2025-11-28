from typing import Protocol, Optional
from abc import abstractmethod
from uuid import UUID
from datetime import datetime

from app.domain.entities import ChargeSettingVersion, PriceRangeTier


class IChargeSettingVersionRepository(Protocol):
    """
    Repository interface for ChargeSettingVersion entities.
    Handles version-specific queries and operations.
    """

    @abstractmethod
    async def get_by_id(self, version_id: UUID) -> ChargeSettingVersion:
        """Retrieve a specific version by ID"""
        ...

    @abstractmethod
    async def get_current_version(
        self, charge_setting_id: UUID
    ) -> Optional[ChargeSettingVersion]:
        """Get the currently active version for a charge setting"""
        ...

    @abstractmethod
    async def get_version_at(
        self, charge_setting_id: UUID, at_time: datetime
    ) -> Optional[ChargeSettingVersion]:
        """Get the version that was active at a specific time"""
        ...

    @abstractmethod
    async def get_version_by_number(
        self, charge_setting_id: UUID, version_number: int
    ) -> Optional[ChargeSettingVersion]:
        """Get a specific version by its number"""
        ...

    @abstractmethod
    async def get_version_history(
        self, charge_setting_id: UUID, limit: Optional[int] = None, offset: int = 0
    ) -> list[ChargeSettingVersion]:
        """
        Get version history for a charge setting.
        Returns versions ordered by version_number descending (newest first).
        """
        ...

    @abstractmethod
    async def add_version(
        self,
        charge_setting_id: UUID,
        tiers: list[PriceRangeTier],
        effective_from: datetime,
        created_by: str,
        change_reason: Optional[str] = None,
    ) -> ChargeSettingVersion:
        """
        Add a new version to a charge setting.
        Automatically closes the previous version and updates version numbering.
        """
        ...

    @abstractmethod
    def save(self, version: ChargeSettingVersion) -> None:
        """Save or update a version"""
        ...

    @abstractmethod
    async def count_versions(self, charge_setting_id: UUID) -> int:
        """Count total versions for a charge setting"""
        ...
