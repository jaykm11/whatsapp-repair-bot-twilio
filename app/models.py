"""
Pydantic models for Twilio WhatsApp webhook payloads
Twilio delivers messages as application/x-www-form-urlencoded POST data
"""

from typing import Optional
from pydantic import BaseModel


class TwilioWebhookPayload(BaseModel):
    """
    Parsed fields from a Twilio WhatsApp webhook POST.
    FastAPI Form() values are mapped here after parsing.
    """
    message_sid: str
    from_: str          # e.g. "whatsapp:+15551234567"
    to: str             # e.g. "whatsapp:+14155238886"
    body: str = ""
    num_media: int = 0
    media_url0: Optional[str] = None
    media_content_type0: Optional[str] = None


class MessageContent(BaseModel):
    """
    Normalised internal message representation passed to the agent layer.
    Decouples agent logic from the raw Twilio payload structure.
    """
    id: str
    from_: str                          # E.164 phone number, no "whatsapp:" prefix
    type: str                           # "text", "image", or "video"
    body: str = ""
    media_url: Optional[str] = None
    media_content_type: Optional[str] = None
