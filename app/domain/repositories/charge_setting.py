from typing import Protocol
from uuid import UUID
from abc import abstractmethod

from app.domain.entities import ChargeSetting


class IChargeSettingRepository(Protocol):
    """
    Repository interface for ChargeSetting aggregate.
    Implementations handle database operations and version management.
    """

    @abstractmethod
    async def get_by_id(self, charge_setting_id: UUID) -> ChargeSetting:
        """Retrieve a charge setting by ID"""
        ...

    @abstractmethod
    async def get_by_type(self, charge_type: str) -> ChargeSetting:
        """Retrieve a charge setting by charge type"""
        ...

    @abstractmethod
    def save(self, charge_setting: ChargeSetting) -> None:
        """Save or update a charge setting"""
        ...

    @abstractmethod
    async def list_all(self, active_only: bool = True) -> list[ChargeSetting]:
        """List all charge settings"""
        ...

    @abstractmethod
    async def delete_all(self) -> None: ...
