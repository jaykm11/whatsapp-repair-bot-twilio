"""
Agent Orchestration Layer
Coordinates WhatsApp message handling, media processing, and AI analysis.
"""

import logging
from app.models import MessageContent
from app.services.whatsapp import whatsapp_service
from app.services.gemini import gemini_service
from app.services.professional_matcher import (
    get_profession_type,
    recommend_professionals,
    format_professional_recommendations,
)

logger = logging.getLogger(__name__)


async def process_message(message: MessageContent, sender: str):
    """
    Main orchestration function for processing incoming WhatsApp messages.

    Args:
        message: Normalised message object
        sender:  Sender's E.164 phone number (no whatsapp: prefix)
    """
    try:
        logger.info("Processing message from %s, type: %s", sender, message.type)

        if message.type == "text":
            await handle_text_message(message, sender)
        elif message.type == "image":
            await handle_image_message(message, sender)
        elif message.type == "video":
            await handle_video_message(message, sender)
        else:
            logger.warning("Unsupported message type: %s", message.type)
            await send_unsupported_message(sender)

    except Exception as e:
        logger.error("Error processing message from %s: %s", sender, e, exc_info=True)
        await send_error_message(sender)


async def handle_text_message(message: MessageContent, sender: str):
    """Handle incoming text messages."""
    text_body = message.body.lower().strip()
    logger.info("Text message from %s: %s", sender, text_body)

    if text_body in {"help", "start", "hello", "hi"}:
        welcome_message = """👋 Welcome to Houston Home Repair AI!

I can help diagnose household plumbing and HVAC issues.

*How to use:*
📸 Send me a photo of your household issue
💬 Optionally include a description of the problem

I'll analyze the image and provide:
• Simple explanation for you
• Technical brief for our repair team

*Examples:*
"Here's my leaking pipe"
"AC not cooling properly"
"Water heater making noise"

Send a photo to get started! 🔧"""
        await whatsapp_service.send_text_message(sender, welcome_message)
    else:
        await whatsapp_service.send_text_message(
            sender,
            "Thanks for your message! To diagnose the issue, please send me a photo of the problem. "
            "You can include a description with the photo too. 📸",
        )


async def handle_image_message(message: MessageContent, sender: str):
    """Handle incoming image messages — the main use case."""
    try:
        if not message.media_url:
            logger.error("Image message has no media URL")
            await send_error_message(sender)
            return

        await whatsapp_service.send_text_message(
            sender,
            "🔍 Analyzing your image... This may take a moment.",
        )

        logger.info("Downloading image from Twilio media URL")
        image_bytes = await whatsapp_service.download_media(message.media_url)

        user_description = message.body or ""

        logger.info("Sending image to Gemini for analysis")
        mime_type = message.media_content_type or "image/jpeg"
        analysis = await gemini_service.analyze_image(image_bytes, user_description, mime_type)

        profession_type = get_profession_type(analysis["full_response"])
        severity = analysis.get("severity", "Medium")

        logger.info("Issue type: %s, Severity: %s", profession_type, severity)

        recommendations, urgency_note = recommend_professionals(
            profession_type=profession_type,
            severity=severity,
            max_recommendations=3,
        )

        professional_section = format_professional_recommendations(
            recommendations, urgency_note
        )

        homeowner_msg = f"🏠 *Household Issue Diagnosis*\n\n{analysis['homeowner_brief']}"
        pro_msg = f"📋 *For Our Repair Team:*\n\n{analysis['pro_brief']}{professional_section}"

        # Safety truncation — Twilio WhatsApp limit is 1600 chars
        if len(homeowner_msg) > 1550:
            homeowner_msg = homeowner_msg[:1547] + "..."
        if len(pro_msg) > 1550:
            pro_msg = pro_msg[:1547] + "..."

        await whatsapp_service.send_text_message(sender, homeowner_msg)
        await whatsapp_service.send_text_message(sender, pro_msg)
        logger.info("Successfully processed image for %s", sender)

    except Exception as e:
        logger.error("Error handling image message: %s", e, exc_info=True)
        await send_error_message(sender)


async def handle_video_message(message: MessageContent, sender: str):
    """Handle incoming video messages."""
    await whatsapp_service.send_text_message(
        sender,
        "📹 Video received! For best results, please send a clear photo of the issue instead. "
        "I can analyze images more accurately. Thanks! 📸",
    )


async def send_unsupported_message(sender: str):
    """Send message for unsupported content types."""
    await whatsapp_service.send_text_message(
        sender,
        "I can only analyze photos of household issues right now. "
        "Please send an image showing the problem! 📸",
    )


async def send_error_message(sender: str):
    """Send a user-friendly error message."""
    await whatsapp_service.send_text_message(
        sender,
        "⚠️ Sorry, something went wrong while processing your request. "
        "Please try again, or contact us directly at (Houston) 555-REPAIR.",
    )
