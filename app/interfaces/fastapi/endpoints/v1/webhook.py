import json
import logging
import hashlib
import hmac
from fastapi import APIRouter, Request
from datetime import datetime, timezone
from typing import cast, Dict, Any, Type
from uuid import UUID

from app.config import settings
from app.utils.signing import sign_payload
from app.application.dto.base import BaseResponseDTO
from app.application.dto.checkout import CheckoutMetaData
from app.shared.errors import AppError
from app.infrastructure.ports.paystack_adapter import (
    PaystackEvent,
    PaystackTransferSuccessEvent,
    PaystackPersonalAccountResDto,
    ChargeData,
)
from app.domain.events import CompleteWithdrawEvent, CompleteFundingEvent
from app.config import paystack_config

from ...di import EventBusDep, VerifyTicketPurchaseTransactionUseCaseDep

router = APIRouter(
    prefix="/v1/webhook",
    tags=["Webhook"],
)


EVENT_SCHEMAS: Dict[str, Type["PaystackEvent[Any]"]] = {
    "transfer.success": PaystackEvent[PaystackPersonalAccountResDto],
    "charge.success": PaystackEvent[ChargeData],
}

logger = logging.getLogger("paystack-webhook")


@router.post("/paystack", response_model=BaseResponseDTO)
async def process_paystack_event(
    req: Request,
    event_bus: EventBusDep,
    verify_txn_uc: VerifyTicketPurchaseTransactionUseCaseDep,
):
    print(
        f"🔔 Incoming Paystack webhook Date & Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )

    raw_body = await req.body()
    print(f"Raw body received ({len(raw_body)} bytes)")

    signature = req.headers.get("x-paystack-signature")

    if signature is None:
        print("❌ Missing Paystack signature header")
        raise AppError("Missing Paystack signature", 400)

    # Compute HMAC
    computed_hash = hmac.new(
        paystack_config.secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    # Validate signature
    if signature != computed_hash:
        print("❌ Invalid Paystack signature – possible spoof attempt")
        raise AppError("Invalid Paystack signature", 400)

    print("✅ Paystack signature verified")

    # Parse JSON
    try:
        body = await req.json()
    except Exception as e:
        print("❌ Failed to parse webhook JSON")
        raise AppError("Invalid JSON", 400)

    event_type = body.get("event")
    print(f"🔍 Paystack event type: {event_type}")

    if not event_type:
        print("❌ Missing `event` field")
        raise AppError("Missing `event` field in Paystack webhook", 400)

    Schema = EVENT_SCHEMAS.get(event_type)
    if not Schema:
        print(f"⚠ Unsupported Paystack event: {event_type}")
        raise AppError(f"Unsupported Paystack event: {event_type}", 400)

    print(f"📦 Using schema: {Schema.__name__}")

    # Validate strongly typed event
    try:
        parsed: PaystackEvent = Schema.model_validate(body)
        print("✅ Event schema validated successfully")
    except Exception:
        print("❌ Schema validation failed")
        print(f"Received payload: {json.dumps(body)}")
        raise AppError("Invalid event schema", 400)

    # Process supported event
    if parsed.event == "transfer.success":
        transfer_data = cast(PaystackTransferSuccessEvent, parsed.data)
        print(
            f"💸 Transfer success for reference={transfer_data.reference} status={transfer_data.status}"
        )

        if transfer_data.status == "success":
            ev = CompleteWithdrawEvent.create(
                amount=transfer_data.amount / 100,
                ref=transfer_data.reference,
                dest=transfer_data.recipient.details.build_dest(),
                date=transfer_data.transferred_at or transfer_data.updatedAt,
            )
            print(f"📤 Publishing CompleteWithdrawEvent: {ev}")
            await event_bus.publish(ev)

    elif parsed.event == "charge.success":
        charge_data = cast(ChargeData, parsed.data)
        metadata = charge_data.metadata
        print(
            f"Charge Success for reference={charge_data.reference} status={charge_data.status}\n"
            f"Metadata={json.dumps(charge_data.metadata) or "No Metadata"}\n"
            f"Amount={charge_data.amount} paid_at={charge_data.paid_at}\n"
        )

        if metadata and metadata.get("action") == "deposit":
            _ = metadata.pop("referrer")
            expected_signature = metadata.pop("signature")

            if expected_signature:
                sig = sign_payload(metadata, settings.charge_req_key)

                if sig != expected_signature:
                    raise AppError(f"Metadata signature mismatch", 400)

                event = CompleteFundingEvent.create(
                    amount_paid=charge_data.amount / 100,
                    ref=charge_data.reference,
                    date=(
                        charge_data.paid_at.isoformat()
                        if charge_data.paid_at
                        else datetime.now(timezone.utc).isoformat()
                    ),
                )

                print(f"📤 Publishing CompleteWithdrawEvent: {event}")
                await event_bus.publish(event)

        if metadata and metadata.get("action") == "ticket_purchase":
            reference = charge_data.reference
            print(f"🔍 Verifying transaction for reference: {reference}")

            if "referrer" in metadata:
                _ = metadata.pop("referrer")

            checkout_metadata = CheckoutMetaData.model_validate(metadata)

            await verify_txn_uc.execute(
                reference=reference,
                user_id=UUID(checkout_metadata.ticket_charge.user),
                validate_only=False,
            )
            print(f"✅ Transaction verified for reference: {reference}")

    print(f"🎉 Paystack event processed successfully: {parsed.event}")

    return BaseResponseDTO.successful()
