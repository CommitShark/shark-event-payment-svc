from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

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
    __slots__ = ("slug",)
    SLUG_FIELD_NUMBER: _ClassVar[int]
    slug: str
    def __init__(self, slug: _Optional[str] = ...) -> None: ...

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
