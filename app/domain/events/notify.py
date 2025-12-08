import zoneinfo
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any, ClassVar, TYPE_CHECKING
from app.shared.errors import AppError
from app.utils.money_utils import format_currency

from .base import DomainEvent

if TYPE_CHECKING:
    from app.domain.entities import Transaction


CHANNEL = Literal["EMAIL", "SMS", "PUSH", "IN_APP"]

user_tz = zoneinfo.ZoneInfo("Africa/Lagos")  # TODO: Store timezone in db


class NotifyPayload(BaseModel):
    channel: CHANNEL = Field(..., description="Channel to send the notification to")
    user_id: str = Field(..., description="ID of the user to notify")

    subject: Optional[str] = Field(
        None, description="Subject/title of the notification"
    )

    message: Optional[str] = Field(None, description="Plain text message content")
    html: Optional[str] = Field(None, description="HTML email body (email only)")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    template: Optional[str] = Field(None, description="Template name or ID to use")

    # Optional: event type or category of notification
    type: Optional[str] = Field(None, description="Notification type identifier")


class NotifyEvent(DomainEvent[NotifyPayload]):
    _event_name: ClassVar[str] = "requested"
    _group: ClassVar[str] = "notification"

    @classmethod
    def withdrawal_complete(cls, txn: "Transaction") -> "NotifyEvent":
        dest = txn.metadata.get("dest", None) if txn.metadata else None
        completion_date_str = (
            txn.metadata.get("completed_at", None) if txn.metadata else None
        )

        if dest is None:
            raise AppError("Destination not set", 500)

        if completion_date_str is None:
            raise AppError("Completion date not set", 500)

        completion_date = (
            datetime.fromisoformat(completion_date_str)
            .astimezone(user_tz)
            .strftime("%A, %B %d • %-I:%M %p")
        )

        return cls(
            aggregate_id=str(txn.reference),
            payload=NotifyPayload(
                channel="EMAIL",
                user_id=str(txn.user_id),
                type="withdrawal_complete",
                subject="Withdrawal complete",
                html=None,
                data={
                    "amount": format_currency(txn.amount),
                    "reference_id": txn.reference,
                    "destination": dest,
                    "date": completion_date,
                },
                message=None,
                template="withdrawal-complete",
            ),
        )

    @classmethod
    def manual_withdrawal_initiated(cls, txn: "Transaction") -> list["NotifyEvent"]:
        dest = txn.metadata.get("dest", None) if txn.metadata else None

        if dest is None:
            raise AppError("Destination not set", 500)

        date = txn.created_at.astimezone(user_tz).strftime("%A, %B %d • %-I:%M %p")

        return [
            cls(
                aggregate_id=str(txn.reference),
                payload=NotifyPayload(
                    channel="EMAIL",
                    user_id="admin",
                    type="withdrawal_initiated",
                    subject="Withdrawal initiated",
                    html=None,
                    data={
                        "amount": f"{format_currency(
                            txn.amount
                        )} + Fees ({format_currency(txn.charge_data.charge_amount if txn.charge_data else 0)})",
                        "reference_id": txn.reference,
                        "destination": dest,
                        "date": date,
                        "user_id": str(txn.user_id),
                    },
                    message=None,
                    template="withdrawal-initiated-admin",
                ),
            ),
            cls(
                aggregate_id=str(txn.reference),
                payload=NotifyPayload(
                    channel="EMAIL",
                    user_id=str(txn.user_id),
                    type="withdrawal_initiated",
                    subject="Withdrawal initiated",
                    html=None,
                    data={
                        "amount": f"{format_currency(
                            txn.amount
                        )} + Fees ({format_currency(txn.charge_data.charge_amount if txn.charge_data else 0)})",
                        "reference_id": txn.reference,
                        "destination": dest,
                        "date": date,
                        "mode": "Manual",
                    },
                    message=None,
                    template="withdrawal-initiated",
                ),
            ),
        ]

    @classmethod
    def manual_withdrawal_failed(cls, txn: "Transaction", reason: str) -> "NotifyEvent":
        dest = txn.metadata.get("dest", None) if txn.metadata else None
        failed_on_str = txn.metadata.get("failed_on") if txn.metadata else None

        if dest is None:
            raise AppError("Destination not set", 500)
        if failed_on_str is None:
            raise AppError("Failed on is not set", 500)

        date = (
            datetime.fromisoformat(failed_on_str)
            .astimezone(user_tz)
            .strftime("%A, %B %d • %-I:%M %p")
        )

        return cls(
            aggregate_id=str(txn.reference),
            payload=NotifyPayload(
                channel="EMAIL",
                user_id=str(txn.user_id),
                type="withdrawal_failed",
                subject="Withdrawal failed",
                html=None,
                data={
                    "amount": f"{format_currency(
                            txn.amount
                        )} + Fees ({format_currency(txn.charge_data.charge_amount if txn.charge_data else 0)})",
                    "reference_id": txn.reference,
                    "destination": dest,
                    "date": date,
                    "reason": reason,
                },
                message=None,
                template="withdrawal-failed",
            ),
        )
