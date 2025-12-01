from typing import cast
from aiobreaker import CircuitBreaker  # type: ignore
from datetime import timedelta

from app.shared.errors import AppError
from app.domain.ports import IUserService

from ..grpc import user_pb2_grpc, user_pb2


cb = CircuitBreaker(
    fail_max=10,
    timeout_duration=timedelta(seconds=60),
    exclude=[AppError],
)


class GrpcUserService(IUserService):
    def __init__(
        self,
        user_stub: user_pb2_grpc.GrpcUserServiceStub,
    ) -> None:
        self._user_stub = user_stub

    @cb
    async def get_event_organizer(self, slug: str) -> str:
        grpc_res = await self._user_stub.GetEventOrganizer(
            user_pb2.GetEventOrganizerRequest(slug=slug)
        )
        grpc_res = cast(user_pb2.GetEventOrganizerResponse, grpc_res)
        if grpc_res.error.strip():
            raise AppError(grpc_res.error, 500)
        return grpc_res.user_id

    @cb
    async def get_system_user_id(self) -> str:
        grpc_res = await self._user_stub.GetSystemUser(user_pb2.GetSystemUserRequest())
        grpc_res = cast(user_pb2.GetSystemUserResponse, grpc_res)
        if grpc_res.error.strip():
            raise AppError(grpc_res.error, 500)
        return grpc_res.user_id

    @cb
    async def get_referral_info(self, user_id: str) -> str | None:
        grpc_res = await self._user_stub.GetReferralInfo(
            user_pb2.GetReferralInfoRequest(user_id=user_id)
        )
        grpc_res = cast(user_pb2.GetReferralInfoResponse, grpc_res)
        if grpc_res.error.strip():
            raise AppError(grpc_res.error, 500)
        return grpc_res.user_id
