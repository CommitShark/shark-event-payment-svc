from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ResolveUserRequest(_message.Message):
    __slots__ = ("email", "first_name", "last_name")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FIRST_NAME_FIELD_NUMBER: _ClassVar[int]
    LAST_NAME_FIELD_NUMBER: _ClassVar[int]
    email: str
    first_name: str
    last_name: str
    def __init__(self, email: _Optional[str] = ..., first_name: _Optional[str] = ..., last_name: _Optional[str] = ...) -> None: ...

class ResolveUserResponse(_message.Message):
    __slots__ = ("id", "email", "username", "avatar")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    AVATAR_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    username: str
    avatar: str
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., username: _Optional[str] = ..., avatar: _Optional[str] = ...) -> None: ...

class CardMasterUser(_message.Message):
    __slots__ = ("id", "email", "first_name", "last_name", "created_at", "avatar", "preferred_name", "tenants")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FIRST_NAME_FIELD_NUMBER: _ClassVar[int]
    LAST_NAME_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    AVATAR_FIELD_NUMBER: _ClassVar[int]
    PREFERRED_NAME_FIELD_NUMBER: _ClassVar[int]
    TENANTS_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    first_name: str
    last_name: str
    created_at: str
    avatar: str
    preferred_name: str
    tenants: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., first_name: _Optional[str] = ..., last_name: _Optional[str] = ..., created_at: _Optional[str] = ..., avatar: _Optional[str] = ..., preferred_name: _Optional[str] = ..., tenants: _Optional[_Iterable[str]] = ...) -> None: ...

class ListCardMasterUserRequest(_message.Message):
    __slots__ = ("page", "size", "q")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    Q_FIELD_NUMBER: _ClassVar[int]
    page: int
    size: int
    q: str
    def __init__(self, page: _Optional[int] = ..., size: _Optional[int] = ..., q: _Optional[str] = ...) -> None: ...

class ListCardMasterUserResponse(_message.Message):
    __slots__ = ("users", "total", "error")
    USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[CardMasterUser]
    total: int
    error: str
    def __init__(self, users: _Optional[_Iterable[_Union[CardMasterUser, _Mapping]]] = ..., total: _Optional[int] = ..., error: _Optional[str] = ...) -> None: ...

class GetUserDefaultTenantRequest(_message.Message):
    __slots__ = ("user_auth_id",)
    USER_AUTH_ID_FIELD_NUMBER: _ClassVar[int]
    user_auth_id: str
    def __init__(self, user_auth_id: _Optional[str] = ...) -> None: ...

class GetUserDefaultTenantResponse(_message.Message):
    __slots__ = ("error", "tenant_id")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    TENANT_ID_FIELD_NUMBER: _ClassVar[int]
    error: str
    tenant_id: str
    def __init__(self, error: _Optional[str] = ..., tenant_id: _Optional[str] = ...) -> None: ...

class GetUserContactInfoRequest(_message.Message):
    __slots__ = ("user_auth_id",)
    USER_AUTH_ID_FIELD_NUMBER: _ClassVar[int]
    user_auth_id: str
    def __init__(self, user_auth_id: _Optional[str] = ...) -> None: ...

class GetUserContactInfoResponse(_message.Message):
    __slots__ = ("error", "email", "phone", "device")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PHONE_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FIELD_NUMBER: _ClassVar[int]
    error: str
    email: str
    phone: str
    device: str
    def __init__(self, error: _Optional[str] = ..., email: _Optional[str] = ..., phone: _Optional[str] = ..., device: _Optional[str] = ...) -> None: ...

class GetEventOrganizerRequest(_message.Message):
    __slots__ = ("event_id",)
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    event_id: str
    def __init__(self, event_id: _Optional[str] = ...) -> None: ...

class GetEventOrganizerResponse(_message.Message):
    __slots__ = ("error", "user_id")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    error: str
    user_id: str
    def __init__(self, error: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class GetSystemUserRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetSystemUserResponse(_message.Message):
    __slots__ = ("error", "user_id")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    error: str
    user_id: str
    def __init__(self, error: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...

class GetReferralInfoRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class GetReferralInfoResponse(_message.Message):
    __slots__ = ("error", "user_id")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    error: str
    user_id: str
    def __init__(self, error: _Optional[str] = ..., user_id: _Optional[str] = ...) -> None: ...
