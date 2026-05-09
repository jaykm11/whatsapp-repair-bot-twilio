"""
Twilio WhatsApp Service
Handles media downloads and message sending via the Twilio Messaging API.

Key differences from Meta Cloud API:
- Auth: HTTP Basic (Account SID + Auth Token), not Bearer token
- Media: URL is delivered directly in the webhook payload
- Send:  POST to /Accounts/{SID}/Messages.json with form-encoded body
- No "mark as read" concept in Twilio
"""

import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

_TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


class WhatsAppService:
    """Service for interacting with the Twilio WhatsApp API."""

    @property
    def _auth(self):
        return (settings.twilio_account_sid, settings.twilio_auth_token)

    @property
    def _messages_url(self):
        return f"{_TWILIO_API_BASE}/Accounts/{settings.twilio_account_sid}/Messages.json"

    async def download_media(self, media_url: str) -> bytes:
        """
        Download a media file from Twilio's servers.

        Twilio includes the full media URL directly in the webhook payload
        (MediaUrl0, MediaUrl1, …), so no extra lookup step is required.

        Args:
            media_url: Direct Twilio media URL from the webhook

        Returns:
            Media file content as bytes
        """
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Downloading media from: {media_url}")
                response = await client.get(
                    media_url,
                    auth=self._auth,
                    timeout=60.0,
                    follow_redirects=True,
                )
                response.raise_for_status()
                logger.info(f"Media downloaded: {len(response.content)} bytes")
                return response.content

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading media: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading media: {e}")
            raise

    async def send_text_message(self, to: str, message: str) -> dict:
        """
        Send a WhatsApp text message via Twilio.

        Args:
            to:      Recipient E.164 number (with or without "whatsapp:" prefix)
            message: Text body to send

        Returns:
            Twilio API response as dict
        """
        # Ensure the whatsapp: prefix is present
        to_addr = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        from_addr = settings.twilio_whatsapp_number
        if not from_addr.startswith("whatsapp:"):
            from_addr = f"whatsapp:{from_addr}"

        payload = {
            "From": from_addr,
            "To": to_addr,
            "Body": message,
        }

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Sending message to {to_addr}")
                response = await client.post(
                    self._messages_url,
                    data=payload,
                    auth=self._auth,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Message sent — SID: {result.get('sid')}")
                return result

        except httpx.HTTPError as e:
            logger.error(f"Error sending message to {to}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise


# Global service instance
whatsapp_service = WhatsAppService()
