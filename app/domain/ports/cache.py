from typing import Protocol, Optional, Any
from abc import abstractmethod


class ICacheService(Protocol):
    """Protocol defining the required cache interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache by key."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 60) -> None:
        """Set a value in the cache with an optional TTL (in seconds)."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Clear the entire cache."""
        ...
