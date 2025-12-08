import logging
import hashlib
import hmac
from fastapi import APIRouter, Request
from typing import cast

from app.application.dto.base import BaseResponseDTO
from app.shared.errors import AppError
from app.infrastructure.ports.paystack_adapter import (
    PaystackEvent,
    PaystackTransferSuccessEvent,
    PaystackPersonalAccountResDto,
)
from app.domain.events import CompleteWithdrawEvent
from app.config import paystack_config

from ...di import EventBusDep

router = APIRouter(
    prefix="/v1/webhook",
    tags=["Webhook"],
)


EVENT_SCHEMAS = {
    "transfer.success": PaystackEvent[PaystackPersonalAccountResDto],
    # add more as you need...
}

logger = logging.getLogger("paystack-webhook")


@router.post("/paystack", response_model=BaseResponseDTO)
async def process_paystack_event(req: Request, event_bus: EventBusDep):
    logger.info("🔔 Incoming Paystack webhook")

    raw_body = await req.body()
    logger.debug(f"Raw body received ({len(raw_body)} bytes)")

    signature = req.headers.get("x-paystack-signature")
    logger.debug(f"Paystack signature received: {signature}")

    if signature is None:
        logger.warning("❌ Missing Paystack signature header")
        raise AppError("Missing Paystack signature", 400)

    # Compute HMAC
    computed_hash = hmac.new(
        paystack_config.secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    logger.debug(f"Computed HMAC: {computed_hash}")

    # Validate signature
    if signature != computed_hash:
        logger.error("❌ Invalid Paystack signature – possible spoof attempt")
        raise AppError("Invalid Paystack signature", 400)

    logger.info("✅ Paystack signature verified")

    # Parse JSON
    try:
        body = await req.json()
    except Exception as e:
        logger.exception("❌ Failed to parse webhook JSON")
        raise AppError("Invalid JSON", 400)

    logger.debug(f"Webhook JSON: {body}")

    event_type = body.get("event")
    logger.info(f"🔍 Paystack event type: {event_type}")

    if not event_type:
        logger.warning("❌ Missing `event` field")
        raise AppError("Missing `event` field in Paystack webhook", 400)

    Schema = EVENT_SCHEMAS.get(event_type)
    if not Schema:
        logger.warning(f"⚠ Unsupported Paystack event: {event_type}")
        raise AppError(f"Unsupported Paystack event: {event_type}", 400)

    logger.info(f"📦 Using schema: {Schema.__name__}")

    # Validate strongly typed event
    try:
        parsed: PaystackEvent = Schema.model_validate(body)
        logger.info("✅ Event schema validated successfully")
    except Exception:
        logger.exception("❌ Schema validation failed")
        raise AppError("Invalid event schema", 400)

    logger.debug(f"Parsed event: {parsed}")

    # Process supported event
    if parsed.event == "transfer.success":
        data = cast(PaystackTransferSuccessEvent, parsed.data)
        logger.info(
            f"💸 Transfer success for reference={data.reference} status={data.status}"
        )

        if data.status == "success":
            ev = CompleteWithdrawEvent.create(
                amount=data.amount / 100,
                ref=data.reference,
                dest=data.recipient.details.build_dest(),
                date=data.transferred_at or data.updatedAt,
            )
            logger.info(f"📤 Publishing CompleteWithdrawEvent: {ev}")
            await event_bus.publish(ev)

    logger.info(f"🎉 Paystack event processed successfully: {parsed.event}")

    return BaseResponseDTO.successful()
