import asyncio
from grpc import RpcError, StatusCode  # type: ignore
from typing import cast
from aiobreaker import CircuitBreaker, CircuitBreakerState  # type: ignore
from decimal import Decimal
from datetime import timedelta
from uuid import UUID

from app.shared.errors import AppError
from app.domain.dto.extra import ExtraOrderDto
from app.domain.ports import ITicketService

from ..grpc import ticketing_pb2_grpc, ticketing_pb2

AUTHORITY_DEADLINE_SECONDS = 0.5
GRPC_DEADLINE_SECONDS = 2

cb = CircuitBreaker(
    fail_max=10,
    timeout_duration=timedelta(seconds=60),
    exclude=[AppError],
)


class GrpcTicketService(ITicketService):
    def __init__(
        self,
        ticket_stub: ticketing_pb2_grpc.GrpcTicketingServiceStub,
    ) -> None:
        self._ticket_stub = ticket_stub

    async def mark_reservation_as_paid(
        self,
        reservation_id: str,
        amount: Decimal,
    ):
        if cb.current_state == CircuitBreakerState.OPEN:
            raise AppError(
                "Ticket services is currently unavailable, try again later", 503
            )

        request = ticketing_pb2.MarkReservationAsPaidRequest(
            reservation_id=reservation_id,
            ticket_amount=str(amount),
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.MarkReservationAsPaid(request),
                    timeout=GRPC_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.MarkReservationAsPaidResponse, grpc_res)

            if grpc_res.error.strip():
                raise AppError(grpc_res.error, 500)
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

    async def cancel_reservation(self, reservation_id: str):
        if cb.current_state == CircuitBreakerState.OPEN:
            raise AppError(
                "Ticket services is currently unavailable, try again later", 503
            )

        request = ticketing_pb2.CancelReservationRequest(
            reservation_id=reservation_id,
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.CancelReservation(request),
                    timeout=GRPC_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.CancelReservationResponse, grpc_res)

            if grpc_res.error.strip():
                raise AppError(grpc_res.error, 500)
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

    async def get_reservation_extra_orders(
        self,
        reservation_id: str,
    ) -> list[ExtraOrderDto]:
        if cb.current_state == CircuitBreakerState.OPEN:
            raise AppError(
                "Ticket services is currently unavailable, try again later", 503
            )

        request = ticketing_pb2.GetReservationExtraOrdersRequest(
            reservation_id=reservation_id,
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.GetReservationExtraOrders(request),
                    timeout=GRPC_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.GetReservationExtraOrdersResponse, grpc_res)

            if grpc_res.error.strip():
                print(f"Error: {grpc_res.error}")
                raise AppError(grpc_res.error, 500)

            return [
                ExtraOrderDto(
                    extra_id=UUID(e.extra_id),
                    extra_version=e.extra_version,
                    quantity=e.quantity,
                    recipient=UUID(e.recipient),
                    unit_price=Decimal(e.unit_price),
                )
                for e in grpc_res.orders
            ]
        except asyncio.TimeoutError:
            raise AppError("Request timed out", 504)
        except RpcError as e:
            print(f"RPC Error: {e.details()}")

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
            raise AppError(f"Unexpected error occurred: {e}", 500)

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
                    timeout=GRPC_DEADLINE_SECONDS,
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

    async def create_gate_ticket(
        self,
        ticket_type_id: str,
        user_id: str,
        occurrence_id: str,
        amount: Decimal,
    ) -> str:
        if cb.current_state == CircuitBreakerState.OPEN:
            raise AppError(
                "Ticket services is currently unavailable, try again later", 503
            )

        request = ticketing_pb2.CreateGateTicketRequest(
            ticket_type_id=ticket_type_id,
            occurrence_id=occurrence_id,
            user_id=user_id,
            amount=str(amount),
        )

        try:

            async def grpc_call_with_timeout():
                return await asyncio.wait_for(
                    self._ticket_stub.CreateGateTicket(request),
                    timeout=GRPC_DEADLINE_SECONDS,
                )

            grpc_res = await cb.call_async(grpc_call_with_timeout)
            grpc_res = cast(ticketing_pb2.CreateGateTicketResponse, grpc_res)

            if grpc_res.error.strip():
                raise AppError(grpc_res.error, 500)

            return grpc_res.qr
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
