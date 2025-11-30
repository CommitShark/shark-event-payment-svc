from typing import Protocol, Optional
from abc import abstractmethod


class IUserService(Protocol):
    @abstractmethod
    async def get_event_organizer(self, ticket_type_id: str) -> str: ...

    @abstractmethod
    async def get_system_user_id(self) -> str: ...

    @abstractmethod
    async def get_referral_info(self, user_id: str) -> Optional[str]: ...
