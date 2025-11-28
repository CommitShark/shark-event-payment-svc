import json
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Generic, TypeVar, ClassVar, Type, Self

# Generic type for strong typing
T = TypeVar("T")


class DomainEvent(BaseModel, Generic[T]):
    """Base event with Pydantic validation"""

    _group: ClassVar[str]
    _event_name: ClassVar[str]

    event_id: UUID = Field(default_factory=uuid4)
    aggregate_id: str  # ID of the aggregate root
    occurred_on: datetime = Field(default_factory=datetime.now)
    version: int = 1
    payload: T  # Domain-specific payload

    class Config:
        frozen = True
        json_encoders = {
            Decimal: str,
            datetime: lambda dt: dt.isoformat(),
        }

    @classmethod
    def from_json(
        cls: Type[Self],
        json_data: str | bytes | bytearray,
    ) -> Self:
        """Deserialize JSON data into a DomainEvent instance.

        Args:
            json_data: JSON string or bytes to deserialize

        Returns:
            DomainEvent instance with the deserialized data
        """
        data = json.loads(json_data)
        return cls.model_validate(data)

    @property
    def event_type(self) -> str:
        return f"{self._group}.{self._event_name}"

    def to_json(self) -> str:
        """Serialize the DomainEvent instance to a JSON string.

        Returns:
            JSON string representation of the DomainEvent
        """
        base_json = self.model_dump_json()
        data = json.loads(base_json)
        data["event_type"] = self.event_type
        return json.dumps(data)

    def to_dict(self) -> dict:
        """Serialize the DomainEvent instance to a Dict.

        Returns:
            Dict representation of the DomainEvent
        """
        dict = self.model_dump()
        dict["event_type"] = self.event_type
        return dict
