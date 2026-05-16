"""Build app/services/agent.py for dev branch (Firestore + Memory Bank)."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "app" / "services" / "agent.py"

text = subprocess.run(
    ["git", "show", "origin/main:app/services/agent.py"],
    capture_output=True,
    check=True,
    cwd=ROOT,
).stdout.decode("utf-8")

IMPORT = "from app.services.memory_bank import memory_bank_service\n"
if IMPORT not in text:
    text = text.replace(
        "from app.services.conversation_store import conversation_store\n",
        "from app.services.conversation_store import conversation_store\n" + IMPORT,
    )

old = '''async def handle_text_message(message: MessageContent, sender: str):
    """Handle incoming text messages."""
    text_body = message.body.lower().strip()
    logger.info("Text message from %s: %s", sender, text_body)

    if text_body in {"help", "start", "hello", "hi"}:'''
new = '''async def handle_text_message(message: MessageContent, sender: str):
    """Handle incoming text messages."""
    raw = (message.body or "").strip()
    text_body = raw.lower()
    logger.info("Text message from %s: %s", sender, text_body[:80])

    if text_body in {"help", "start", "hello", "hi"}:'''
if "raw = (message.body" not in text:
    text = text.replace(old, new, 1)

old = '''        await whatsapp_service.send_text_message(sender, welcome_message)
    else:
        await whatsapp_service.send_text_message(
            sender,
            "Thanks for your message! To diagnose the issue, please send me a photo of the problem. "
            "You can include a description with the photo too. 📸",
        )'''
new = '''        await conversation_store.append_turn(sender, "user", raw or text_body)
        await conversation_store.append_turn(sender, "assistant", welcome_message)
        await whatsapp_service.send_text_message(sender, welcome_message)
        return

    prior = await conversation_store.get_prior_turns(sender)
    memory_facts = await memory_bank_service.retrieve_facts(sender, raw)
    try:
        reply = await gemini_service.chat_reply(prior, raw, memory_facts=memory_facts)
    except Exception as e:
        logger.error("Conversational reply failed: %s", e, exc_info=True)
        reply = (
            "I had trouble thinking that through—please try again in a moment, "
            "or send a photo of the issue so I can diagnose it. 📸"
        )
    await conversation_store.append_turn(sender, "user", raw)
    await conversation_store.append_turn(sender, "assistant", reply)
    await whatsapp_service.send_text_message(sender, reply)
    await memory_bank_service.record_exchange(
        sender,
        [{"role": "user", "content": raw}, {"role": "assistant", "content": reply}],
    )'''
if "memory_bank_service" not in text:
    text = text.replace(old, new, 1)

old = '''        await whatsapp_service.send_text_message(
            sender,
            "🔍 Analyzing your image... This may take a moment.",
        )

        logger.info("Downloading image from Twilio media URL")
        image_bytes = await whatsapp_service.download_media(message.media_url)

        user_description = message.body or ""'''
new = '''        user_description = (message.body or "").strip()
        photo_note = "[Sent a photo]"
        if user_description:
            photo_note = f"[Sent a photo — note: {user_description}]"
        await conversation_store.append_turn(sender, "user", photo_note)

        await whatsapp_service.send_text_message(
            sender,
            "🔍 Analyzing your image... This may take a moment.",
        )

        logger.info("Downloading image from Twilio media URL")
        image_bytes = await whatsapp_service.download_media(message.media_url)'''
if "photo_note" not in text:
    text = text.replace(old, new, 1)

old = '''        await whatsapp_service.send_text_message(sender, homeowner_msg)
        await whatsapp_service.send_text_message(sender, pro_msg)
        logger.info("Successfully processed image for %s", sender)'''
new = '''        await whatsapp_service.send_text_message(sender, homeowner_msg)
        await whatsapp_service.send_text_message(sender, pro_msg)

        memory_summary = (analysis.get("homeowner_brief") or "").strip()
        if len(memory_summary) > 400:
            memory_summary = memory_summary[:397] + "..."
        if memory_summary:
            await conversation_store.append_turn(
                sender,
                "assistant",
                f"(Diagnosis from your photo) {memory_summary}",
            )
            await memory_bank_service.record_exchange(
                sender,
                [
                    {"role": "user", "content": photo_note},
                    {"role": "assistant", "content": f"(Diagnosis) {memory_summary}"},
                ],
            )

        logger.info("Successfully processed image for %s", sender)'''
if "memory_summary" not in text:
    text = text.replace(old, new, 1)

AGENT.write_text(text, encoding="utf-8", newline="\n")
print("Wrote", AGENT)
