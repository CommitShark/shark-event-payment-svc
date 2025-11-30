import asyncio
from grpc import RpcError, StatusCode  # type: ignore
from typing import cast
from aiobreaker import CircuitBreaker, CircuitBreakerState  # type: ignore
from decimal import Decimal
from datetime import timedelta

from app.shared.errors import AppError
from app.domain.ports import ITicketService

from ..grpc import ticketing_pb2_grpc, ticketing_pb2

AUTHORITY_DEADLINE_SECONDS = 0.5

cb = CircuitBreaker(
    fail_max=10, timeout_duration=timedelta(seconds=60), exclude=[AppError]
)


class GrpcTicketService(ITicketService):
    def __init__(
        self,
        ticket_stub: ticketing_pb2_grpc.GrpcTicketingServiceStub,
    ) -> None:
        self._ticket_stub = ticket_stub

    async def reservation_is_valid(
        self, reservation_id: str
    ) -> tuple[bool, str | None]:
        if cb.current_state == CircuitBreakerState.OPEN:
            return False, "Ticket services is currently unavailable, try again later"

        request = ticketing_pb2.CheckReservationRequest(
            reservation_id=reservation_id,
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.CheckReservation(request),
                    timeout=AUTHORITY_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.CheckReservationResponse, grpc_res)

            if grpc_res.error.strip():
                return False, grpc_res.error

            if not grpc_res.exists:
                return False, "Reservation not found"

            if not grpc_res.valid:
                return False, "Invalid or expired reservation"

            return True, None
        except asyncio.TimeoutError:
            raise AppError("Request timed out", 504)
        except RpcError as e:
            # Map gRPC errors to appropriate HTTP status codes
            error_map = {
                StatusCode.UNAVAILABLE: (503, "Service unavailable"),
                StatusCode.DEADLINE_EXCEEDED: (504, "Request deadline exceeded"),
                StatusCode.NOT_FOUND: (404, "Ticket type not found"),
                StatusCode.INVALID_ARGUMENT: (400, "Invalid ticket type"),
                StatusCode.UNAUTHENTICATED: (401, "Authentication required"),
                StatusCode.PERMISSION_DENIED: (403, "Permission denied"),
            }

            status_code, message = error_map.get(
                e.code(), (500, f"gRPC error: {e.details()}")
            )
            raise AppError(message, status_code)

        except Exception as e:
            # Catch any other errors
            raise AppError(f"Unexpected error: {str(e)}", 500)

    async def get_ticket_price(self, ticket_type_id: str) -> Decimal:
        if cb.current_state == CircuitBreakerState.OPEN:
            raise AppError(
                "Ticket services is currently unavailable, try again later", 503
            )

        request = ticketing_pb2.GetTicketPriceRequest(
            ticket_type_id=ticket_type_id,
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.GetTicketPrice(request),
                    timeout=AUTHORITY_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.GetTicketPriceResponse, grpc_res)

            if grpc_res.error.strip():
                raise AppError(grpc_res.error, 500)

            return Decimal(grpc_res.amount)
        except asyncio.TimeoutError:
            raise AppError("Request timed out", 504)
        except RpcError as e:
            # Map gRPC errors to appropriate HTTP status codes
            error_map = {
                StatusCode.UNAVAILABLE: (503, "Service unavailable"),
                StatusCode.DEADLINE_EXCEEDED: (504, "Request deadline exceeded"),
                StatusCode.NOT_FOUND: (404, "Ticket type not found"),
                StatusCode.INVALID_ARGUMENT: (400, "Invalid ticket type"),
                StatusCode.UNAUTHENTICATED: (401, "Authentication required"),
                StatusCode.PERMISSION_DENIED: (403, "Permission denied"),
            }

            status_code, message = error_map.get(
                e.code(), (500, f"gRPC error: {e.details()}")
            )
            raise AppError(message, status_code)

        except Exception as e:
            # Catch any other errors
            raise AppError(f"Unexpected error: {str(e)}", 500)
