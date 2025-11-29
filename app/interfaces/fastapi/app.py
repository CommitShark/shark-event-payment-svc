import logging
import grpc  # type: ignore
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import grpc_config
from app.config.http import HttpSettings
from app.config.sqlalchemy import DatabaseSettings
from app.shared.errors import AppError

from app.infrastructure.grpc import ticketing_pb2_grpc
from .endpoints.v1 import charges

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# async def setup_handlers(event_bus: IEventBus):
#     handlers = [
#         EventEventHandler(),
#     ]

#     for handler in handlers:
#         for event_class in handler.events:
#             event_type = cast(Type[DomainEvent[Any]], event_class)
#             await event_bus.subscribe(event_type, handler.handle)
#             print(
#                 f"✅ {handler.__class__.__name__} subscribed to "
#                 f"{event_type._group}:{event_type._event_name}"
#             )


# async def serve_grpc():
#     server = grpc.aio.server()
#     reservation_pb2_grpc.add_GrpcTicketServiceServicer_to_server(
#         TicketServiceServicer(),
#         server,
#     )
#     listen_addr = "[::]:50051"
#     server.add_insecure_port(listen_addr)
#     await server.start()
#     print(f"gRPC Server listening", listen_addr)
#     await server.wait_for_termination()


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Configure app dependencies during startup"""

    # kafka_event_bus = KafkaEventBus(
    #     bootstrap_servers=kafka_config.bootstrap_servers,
    #     group_id=kafka_config.group_id,
    # )

    # app.state.event_bus = kafka_event_bus

    # await setup_handlers(kafka_event_bus)
    # await kafka_event_bus.connect()
    # await kafka_event_bus.start_consuming()

    app.state.ticket_channel = grpc.aio.insecure_channel(grpc_config.ticket_svc_target)
    app.state.ticket_stub = ticketing_pb2_grpc.GrpcTicketingServiceStub(
        app.state.ticket_channel
    )

    logger.info("Application startup complete")

    yield

    # 4. Cleanup
    await app.state.ticket_channel.close()
    # await kafka_event_bus.disconnect()
    # await permify_client.client.aclose()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    DatabaseSettings()
    settings = HttpSettings()

    app = FastAPI(
        root_path=settings.root_path,
        lifespan=app_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(charges.router)

    logger.info(
        "FastAPI application created with root path: %s",
        settings.root_path,
    )

    return app


app = create_app()


@app.exception_handler(AppError)
async def app_exception_handler(_: Request, err: AppError):
    payload = {
        "message": err.message,
        "code": err.error_code,
    }

    if err.payload is not None:
        payload["data"] = err.payload

    return JSONResponse(
        status_code=err.status_code,
        content=payload,
    )


@app.get("/healthz")
async def health_check():
    return {"status": "ok"}
