"""
WhatsApp Home Repair AI Agent - FastAPI Application
Main entry point with Twilio webhook endpoint.

Twilio delivers messages as HTTP POST with application/x-www-form-urlencoded
content (not JSON), so the webhook handler uses FastAPI Form() parameters.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.config import settings
from app.models import MessageContent
from app.services.agent import process_message

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate configuration and log startup status."""
    missing = [
        name
        for name, value in {
            "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
            "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
            "TWILIO_WHATSAPP_NUMBER": settings.twilio_whatsapp_number,
            "GEMINI_API_KEY": settings.gemini_api_key,
        }.items()
        if not value
    ]
    if missing:
        logger.error("Missing required credentials: %s — API calls will fail.", missing)
    else:
        logger.info("All credentials loaded. Service ready.")
    yield


app = FastAPI(
    title="WhatsApp Home Repair AI Agent",
    description="AI-powered household issue diagnosis via WhatsApp (Twilio)",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"status": "healthy", "service": "WhatsApp Home Repair AI Agent"}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "whatsapp-repair-bot",
        "version": "2.0.0",
    }


@app.post("/webhook")
async def handle_webhook(
    request: Request,
    # Core fields present in every Twilio WhatsApp webhook
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
    # Media fields — only present when NumMedia > 0
    MediaUrl0: Optional[str] = Form(None),
    MediaContentType0: Optional[str] = Form(None),
):
    """
    Webhook endpoint for receiving WhatsApp messages via Twilio.

    Twilio sends a POST with form-encoded fields.  We return a 200 with an
    empty TwiML response so Twilio does not retry the request.  Actual
    message processing happens asynchronously via asyncio.create_task().
    """
    try:
        logger.info(
            "Webhook received — SID: %s, From: %s, NumMedia: %d",
            MessageSid, From, NumMedia,
        )

        # Determine message type and build the normalised MessageContent
        sender = From.removeprefix("whatsapp:")   # strip prefix for downstream use

        if NumMedia > 0 and MediaUrl0:
            content_type = (MediaContentType0 or "").lower()
            if "video" in content_type:
                msg_type = "video"
            else:
                msg_type = "image"  # treat audio/docs as image (Gemini handles gracefully)
        elif Body.strip():
            msg_type = "text"
        else:
            logger.warning("Empty message from %s — ignoring", sender)
            return PlainTextResponse("", status_code=200)

        message = MessageContent(
            id=MessageSid,
            from_=sender,
            type=msg_type,
            body=Body,
            media_url=MediaUrl0,
            media_content_type=MediaContentType0,
        )

        # Process asynchronously — Twilio expects a fast 200 response
        asyncio.create_task(process_message(message, sender))

        # Empty 200 TwiML response tells Twilio not to send any automatic reply
        return PlainTextResponse("", status_code=200)

    except Exception as e:
        logger.error("Error handling webhook: %s", e, exc_info=True)
        # Still return 200 so Twilio doesn't keep retrying
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
