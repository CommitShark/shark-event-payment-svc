from typing import Dict, Type, ClassVar, TypeVar
from .base import DomainEvent

T = TypeVar("T", bound=Type[DomainEvent])


class EventRegistry:
    """Type-safe event registry with validation"""

    _registry: ClassVar[Dict[str, Type[DomainEvent]]] = {}

    @classmethod
    def register(cls, event_class: T) -> T:
        """Decorator to register event classes"""
        event_key = f"{event_class._group}.{event_class._event_name}"

        if event_key in cls._registry:
            raise ValueError(f"Event {event_key} is already registered")

        cls._registry[event_key] = event_class
        return event_class

    @classmethod
    def get_event_class(cls, event_key: str) -> Type[DomainEvent]:
        """Get event class by key"""
        if event_key not in cls._registry:
            raise KeyError(f"Event {event_key} not found in registry")
        return cls._registry[event_key]

    @classmethod
    def get_event_key(cls, event_class: Type[DomainEvent]) -> str:
        """Get event key from event class"""
        return f"{event_class._group}.{event_class._event_name}"

    @classmethod
    def get_all_events(cls) -> Dict[str, Type[DomainEvent]]:
        """Get all registered events"""
        return cls._registry.copy()
