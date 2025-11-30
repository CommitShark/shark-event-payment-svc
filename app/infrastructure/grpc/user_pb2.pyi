from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class GetEventOrganizerRequest(_message.Message):
    __slots__ = ("ticket_type_id",)
    TICKET_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    ticket_type_id: str
    def __init__(self, ticket_type_id: _Optional[str] = ...) -> None: ...

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
