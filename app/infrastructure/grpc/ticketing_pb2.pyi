import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListOccurrenceTicketUsersRequest(_message.Message):
    __slots__ = ("occurrence_id",)
    OCCURRENCE_ID_FIELD_NUMBER: _ClassVar[int]
    occurrence_id: str
    def __init__(self, occurrence_id: _Optional[str] = ...) -> None: ...

class ListOccurrenceTicketUsersResponse(_message.Message):
    __slots__ = ("user_ids",)
    USER_IDS_FIELD_NUMBER: _ClassVar[int]
    user_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, user_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class CreateGateTicketRequest(_message.Message):
    __slots__ = ("ticket_type_id", "user_id", "occurrence_id", "amount")
    TICKET_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    OCCURRENCE_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    ticket_type_id: str
    user_id: str
    occurrence_id: str
    amount: str
    def __init__(self, ticket_type_id: _Optional[str] = ..., user_id: _Optional[str] = ..., occurrence_id: _Optional[str] = ..., amount: _Optional[str] = ...) -> None: ...

class CreateGateTicketResponse(_message.Message):
    __slots__ = ("qr", "error")
    QR_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    qr: str
    error: str
    def __init__(self, qr: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class CancelReservationRequest(_message.Message):
    __slots__ = ("reservation_id",)
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    reservation_id: str
    def __init__(self, reservation_id: _Optional[str] = ...) -> None: ...

class CancelReservationResponse(_message.Message):
    __slots__ = ("error",)
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...

class MarkReservationAsPaidRequest(_message.Message):
    __slots__ = ("reservation_id", "ticket_amount")
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    TICKET_AMOUNT_FIELD_NUMBER: _ClassVar[int]
    reservation_id: str
    ticket_amount: str
    def __init__(self, reservation_id: _Optional[str] = ..., ticket_amount: _Optional[str] = ...) -> None: ...

class ExtraOrderDto(_message.Message):
    __slots__ = ("extra_id", "extra_version", "quantity", "unit_price", "recipient")
    EXTRA_ID_FIELD_NUMBER: _ClassVar[int]
    EXTRA_VERSION_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    UNIT_PRICE_FIELD_NUMBER: _ClassVar[int]
    RECIPIENT_FIELD_NUMBER: _ClassVar[int]
    extra_id: str
    extra_version: int
    quantity: int
    unit_price: str
    recipient: str
    def __init__(self, extra_id: _Optional[str] = ..., extra_version: _Optional[int] = ..., quantity: _Optional[int] = ..., unit_price: _Optional[str] = ..., recipient: _Optional[str] = ...) -> None: ...

class GetReservationExtraOrdersRequest(_message.Message):
    __slots__ = ("reservation_id",)
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    reservation_id: str
    def __init__(self, reservation_id: _Optional[str] = ...) -> None: ...

class GetReservationExtraOrdersResponse(_message.Message):
    __slots__ = ("error", "orders")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    ORDERS_FIELD_NUMBER: _ClassVar[int]
    error: str
    orders: _containers.RepeatedCompositeFieldContainer[ExtraOrderDto]
    def __init__(self, error: _Optional[str] = ..., orders: _Optional[_Iterable[_Union[ExtraOrderDto, _Mapping]]] = ...) -> None: ...

class MarkReservationAsPaidResponse(_message.Message):
    __slots__ = ("error",)
    ERROR_FIELD_NUMBER: _ClassVar[int]
    error: str
    def __init__(self, error: _Optional[str] = ...) -> None: ...

class GetTicketPriceRequest(_message.Message):
    __slots__ = ("ticket_type_id",)
    TICKET_TYPE_ID_FIELD_NUMBER: _ClassVar[int]
    ticket_type_id: str
    def __init__(self, ticket_type_id: _Optional[str] = ...) -> None: ...

class GetTicketPriceResponse(_message.Message):
    __slots__ = ("error", "amount")
    ERROR_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    error: str
    amount: str
    def __init__(self, error: _Optional[str] = ..., amount: _Optional[str] = ...) -> None: ...

class CheckReservationRequest(_message.Message):
    __slots__ = ("reservation_id",)
    RESERVATION_ID_FIELD_NUMBER: _ClassVar[int]
    reservation_id: str
    def __init__(self, reservation_id: _Optional[str] = ...) -> None: ...

class Reservation(_message.Message):
    __slots__ = ("id", "user_id", "created_at", "expires_at", "status")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    created_at: _timestamp_pb2.Timestamp
    expires_at: _timestamp_pb2.Timestamp
    status: str
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., expires_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., status: _Optional[str] = ...) -> None: ...

class CheckReservationResponse(_message.Message):
    __slots__ = ("exists", "valid", "reservation", "error")
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    VALID_FIELD_NUMBER: _ClassVar[int]
    RESERVATION_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    valid: bool
    reservation: Reservation
    error: str
    def __init__(self, exists: bool = ..., valid: bool = ..., reservation: _Optional[_Union[Reservation, _Mapping]] = ..., error: _Optional[str] = ...) -> None: ...
