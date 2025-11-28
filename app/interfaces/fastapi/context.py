from fastapi import Depends, Request, HTTPException, Header
from fastapi.security import APIKeyCookie

from typing import Annotated, Optional, Any
from uuid import UUID
from pydantic import BaseModel

vid_scheme = APIKeyCookie(name="vid")
token_scheme = APIKeyCookie(name="access_token")


class UserContext(BaseModel):
    user_id: UUID


def get_tenant_id(
    tenant_id_header: Annotated[
        str,
        Header(alias="X-Tenant-ID"),
    ],
) -> UUID:
    if not tenant_id_header:
        raise HTTPException(
            status_code=403,
            detail="Missing tenant id (workspace) header",
        )
    return UUID(tenant_id_header)


def get_user_context(request: Request) -> UserContext:
    """Extract user context from API gateway headers"""

    # Common header names used by API gateways
    user_id_header = request.headers.get("X-User-ID")

    # Validate required headers
    if not user_id_header:
        raise HTTPException(
            status_code=401,
            detail="Missing user ID header - authentication required",
        )

    try:
        # Let Pydantic handle validation and type conversion
        return UserContext(
            user_id=UUID(user_id_header),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid user context data: {str(e)}"
        )


def get_optional_user_context(request: Request) -> Optional[UserContext]:
    """Extract user context from headers, return None if not authenticated"""
    try:
        return get_user_context(request)
    except HTTPException:
        return None


def get_visitor_id(
    credentials=Depends(vid_scheme),
):
    vid = credentials

    if not vid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request, session is malformed",
        )

    return vid


def get_access_token(
    access_token=Depends(token_scheme),
):
    token = access_token

    if not token:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request, session is malformed",
        )

    return token


# Type annotations for dependency injection
UserContextDep = Annotated[UserContext, Depends(get_user_context)]
OptionalUserContextDep = Annotated[
    UserContext | None, Depends(get_optional_user_context)
]
TenantIDDep = Annotated[UUID, Depends(get_tenant_id)]
VisitorIdDep = Annotated[str, Depends(get_visitor_id)]
ProtectedDep = Annotated[str, Depends(get_access_token)]
