from typing import Optional, Any
from enum import Enum


class ErrorCodes(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    REFERRAL_PROFILE_NOT_FOUND = "REFERRAL_PROFILE_NOT_FOUND"
    ROLE_NOT_FOUND = "ROLE_NOT_FOUND"
    ONBOARDING_INCOMPLETE = "ONBOARDING_INCOMPLETE"
    NO_DEFAULT_WORKPLACE = "NO_DEFAULT_WORKPLACE"
    GENERIC = "GENERIC"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    COULD_NOT_GENERATE_CHARGE = "COULD_NOT_GENERATE_CHARGE"
    INVALID_TXN_PIN = "INVALID_TXN_PIN"


class AppError(Exception):
    """Base class for an App Error"""

    status_code: int
    message: str
    payload: Optional[Any]
    error_code: Optional[ErrorCodes]

    def __init__(
        self,
        message: str,
        status_code: int,
        payload: Optional[Any] = None,
        error_code: Optional[ErrorCodes] = ErrorCodes.GENERIC,
    ):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
        self.error_code = error_code

    def to_dict(self):
        error_data = dict(self.payload or {})
        error_data["message"] = self.message
        error_data["code"] = self.error_code
        return error_data


class InternalAppError(AppError):
    """Internal Api Error"""

    message: str
    payload: Optional[Any]

    def __init__(
        self,
        message: str,
        payload: Optional[Any] = None,
        code: int = 500,
    ):
        super().__init__(message, code, payload)
