import grpc  # type: ignore
import threading
from app.infrastructure.grpc import ticketing_pb2_grpc, user_pb2_grpc

_init_lock = threading.Lock()
_ticket_stub: ticketing_pb2_grpc.GrpcTicketingServiceStub | None = None
_channel: grpc.aio.Channel | None = None


def init_ticket_grpc_client(host: str):
    global _ticket_stub, _channel
    if _ticket_stub is None:
        with _init_lock:
            if _ticket_stub is None:
                _channel = grpc.aio.insecure_channel(host)
                _ticket_stub = ticketing_pb2_grpc.GrpcTicketingServiceStub(_channel)
    return _ticket_stub


async def close_ticket_grpc_client():
    global _ticket_stub, _channel
    if _ticket_stub and _channel:
        await _channel.close()
        _ticket_stub = None
        _channel = None


def get_ticket_grpc_stub():
    if _ticket_stub is None:
        raise RuntimeError("Ticket gRPC client not initialized")
    return _ticket_stub


_init_user_lock = threading.Lock()
_user_stub: user_pb2_grpc.GrpcUserServiceStub | None = None
_user_channel: grpc.aio.Channel | None = None


def init_user_grpc_client(host: str):
    global _user_stub, _user_channel
    if _user_stub is None:
        with _init_user_lock:
            if _user_stub is None:
                _user_channel = grpc.aio.insecure_channel(host)
                _user_stub = user_pb2_grpc.GrpcUserServiceStub(_user_channel)
    return _user_stub


async def close_user_grpc_client():
    global _user_stub, _user_channel
    if _user_channel and _user_stub:
        await _user_channel.close()
        _user_stub = None
        _user_channel = None


def get_user_grpc_stub():
    if _user_stub is None:
        raise RuntimeError("User gRPC client not initialized")
    return _user_stub
