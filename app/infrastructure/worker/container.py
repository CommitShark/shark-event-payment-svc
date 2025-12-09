from typing import Type, Dict, TypeVar, Any, List, Callable, Set
from app.application.use_cases import (
    ProcessDueSettlementsUseCase,
    SettleTicketPurchaseUseCase,
)
from app.domain.repositories import ITransactionRepository
from app.domain.ports import ITicketService, IUserService, IEventBus
from app.infrastructure.sqlalchemy.repositories import SqlAlchemyTransactionRepository
from app.infrastructure.grpc import grpc_client
from app.infrastructure.ports.kafka_event_bus import kafka_event_bus
from app.config import grpc_config

from .base import IWorker

W = TypeVar("W", bound=IWorker)
T = TypeVar("T")


class DIContainer:
    def __init__(self) -> None:
        self._providers: Dict[Type[Any], Callable[[], Any]] = {}
        self._instances: Dict[Type[Any], Any] = {}
        self._singletons: Set[Type[Any]] = set()

    def register(
        self, iface: Type[T], provider: Callable[[], T], singleton: bool = False
    ) -> None:
        """Register a provider for an interface."""
        self._providers[iface] = provider
        if singleton:
            self._singletons.add(iface)

    def resolve(self, iface: Type[T]) -> T:
        """
        Return an instance for the interface.
        Lazy-instantiate using provider.
        Cache if singleton.
        """
        if iface not in self._providers:
            raise KeyError(f"{iface.__name__} is not registered in DIContainer")

        if iface in self._singletons:
            if iface not in self._instances:
                self._instances[iface] = self._providers[iface]()
            return self._instances[iface]

        # Non-singleton: create a new instance each call
        return self._providers[iface]()

    @staticmethod
    async def init() -> None:
        """Global async initialization for external clients."""
        grpc_client.init_ticket_grpc_client(grpc_config.ticket_svc_target)
        grpc_client.init_user_grpc_client(grpc_config.ticket_svc_target)
        await kafka_event_bus.connect_producer()

    @staticmethod
    async def shutdown() -> None:
        """Global async cleanup for external clients."""
        await grpc_client.close_ticket_grpc_client()
        await grpc_client.close_user_grpc_client()
        await kafka_event_bus.disconnect_producer()


def build_di_container():
    container = DIContainer()

    # Repositories
    container.register(
        ITransactionRepository, lambda: SqlAlchemyTransactionRepository()
    )

    # Ports
    container.register(ITicketService, lambda: grpc_client.get_ticket_grpc_stub(), True)
    container.register(IUserService, lambda: grpc_client.get_user_grpc_stub(), True)
    container.register(IEventBus, lambda: kafka_event_bus, True)

    # Use cases
    container.register(
        SettleTicketPurchaseUseCase,
        lambda: SettleTicketPurchaseUseCase(
            txn_repo=container.resolve(ITransactionRepository),
            ticket_service=container.resolve(ITicketService),
            event_bus=container.resolve(IEventBus),
            user_service=container.resolve(IUserService),
        ),
    )

    container.register(
        ProcessDueSettlementsUseCase,
        lambda: ProcessDueSettlementsUseCase(
            txn_repo=container.resolve(ITransactionRepository),
            settle_use_case=container.resolve(SettleTicketPurchaseUseCase),
        ),
    )

    return container


class WorkerContainer:
    def __init__(self, di: DIContainer) -> None:
        self._di = di
        self._registrations: Dict[Type[IWorker], Type[IWorker]] = {}
        self._instances: Dict[Type[IWorker], IWorker] = {}

    def register(self, cls: Type[W]) -> None:
        self._registrations[cls] = cls

    def resolve(self, cls: Type[W]) -> W:
        if cls not in self._registrations:
            raise KeyError(f"{cls.__name__} is not registered in WorkerContainer")

        if cls not in self._instances:
            # create instance with DI container
            instance = cls(self._di)  # type: ignore
            self._instances[cls] = instance

        return self._instances[cls]  # type: ignore[return-value]

    def resolve_all(self) -> List[IWorker]:
        # Instantiate all, return list of all created workers
        for cls in self._registrations:
            self.resolve(cls)
        return list(self._instances.values())
