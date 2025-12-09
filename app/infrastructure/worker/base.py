from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .container import DIContainer


class IWorker(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Main worker loop."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup resources, stop loop."""
        ...
