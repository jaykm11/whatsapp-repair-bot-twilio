"""
Gemini AI Service
Multimodal image analysis using Google's Gemini 2.5 Flash (google-genai SDK)
"""

import asyncio
import json
import logging
import os

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS = 50


def _load_professionals_summary() -> str:
    """Load professionals.json and format it as a compact directory for the prompt."""
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "professionals.json")
        path = os.path.normpath(path)
        with open(path) as f:
            data = json.load(f)

        lines = ["AVAILABLE PROFESSIONALS DIRECTORY:"]
        category_labels = {
            "plumbers": "Plumbers",
            "hvac": "HVAC Technicians",
            "electricians": "Electricians",
            "handyman": "Handymen",
        }
        for category, label in category_labels.items():
            pros = data.get(category, [])
            if not pros:
                continue
            lines.append(f"\n{label}:")
            for p in pros:
                areas = ", ".join(p.get("areas", []))
                avail = p.get("availability", "Unknown")
                rate = p.get("hourly_rate", "")
                rating = p.get("rating", "")
                phone = p.get("phone", "")
                lines.append(
                    f"  • {p['name']} | Phone: {phone} | Areas: {areas} | "
                    f"Avail: {avail} | Rate: {rate} | Rating: {rating}⭐"
                )
        return "\n".join(lines)
    except Exception as e:
        logger.warning("Could not load professionals.json: %s", e)
        return ""


_PROFESSIONALS_SUMMARY = _load_professionals_summary()

CHAT_SYSTEM = f"""You are a friendly Houston home repair assistant on WhatsApp. \
You help customers find the right repair professional and diagnose plumbing, HVAC, \
electrical, and handyman issues.

{_PROFESSIONALS_SUMMARY}

GUIDELINES:
- When asked about availability, professionals, or who to call in a specific area, \
look up the directory above and give a direct, helpful answer with name, phone, \
availability, and rate. Only list professionals who serve that area.
- Be conversational and warm — like a knowledgeable friend, not a robot.
- Keep replies concise (2-4 sentences or a short list). No walls of text.
- If they need a visual diagnosis, ask them to send a clear photo.
- Reference earlier conversation context when relevant.
- If you are unsure about something, say so honestly."""


class GeminiService:
    """Service for analyzing household issues using Gemini AI"""

    def __init__(self):
        self._client: genai.Client | None = None

        self.system_prompt = """You are a Master Plumber and HVAC Technician with 25+ years of experience diagnosing household issues.

You specialize in identifying plumbing problems (leaks, clogs, pipe damage, water heaters, fixtures) and HVAC issues (heating, cooling, ventilation, ductwork, thermostats).

When analyzing an image, provide TWO distinct responses. Be concise — each section must be under 400 characters.

1. HOMEOWNER BRIEF:
   - 2 sentences max in plain English
   - What the issue is and any immediate safety concern

2. PRO BRIEF:
   - Issue, Severity (Low/Medium/High), key parts needed, estimated time
   - 3-4 bullet points max

Format your response exactly as follows:

**HOMEOWNER BRIEF:**
[2 sentences max]

**PRO BRIEF:**
- **Issue:** [problem]
- **Severity:** [Low/Medium/High]
- **Parts Needed:** [brief list]
- **Estimated Time:** [time]

Keep the total response under 800 characters. If the image doesn't show a plumbing or HVAC issue, respond with one sentence saying so.
"""

    @property
    def client(self) -> genai.Client:
        """Create the Gemini client on first use so startup never crashes."""
        if self._client is None:
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    async def analyze_image(
        self,
        image_bytes: bytes,
        user_message: str = "",
        mime_type: str = "image/jpeg",
    ) -> dict:
        """
        Analyze a household issue from an image.

        Args:
            image_bytes:  Image data as bytes
            user_message: Optional text message from user describing the issue
            mime_type:    MIME type of the image (default image/jpeg)

        Returns:
            dict with 'homeowner_brief', 'pro_brief', 'severity', 'full_response'
        """
        try:
            logger.info(
                "Analyzing image with Gemini %s (%d bytes)", GEMINI_MODEL, len(image_bytes)
            )

            user_context = f"\nUser's description: {user_message}" if user_message else ""
            prompt_text = (
                f"{self.system_prompt}{user_context}\n\nAnalyze the image and provide your diagnosis:"
            )

            contents = [
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt_text,
            ]

            logger.info("Calling Gemini API (timeout=%ds)...", GEMINI_TIMEOUT_SECONDS)

            # Run sync client in thread pool — avoids gRPC async issues on Cloud Run
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=GEMINI_MODEL,
                    contents=contents,
                ),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )

            logger.info("Gemini analysis completed successfully")

            full_response = response.text
            return self._parse_response(full_response)

        except asyncio.TimeoutError:
            logger.error("Gemini API timed out after %ds", GEMINI_TIMEOUT_SECONDS)
            raise RuntimeError(
                f"Gemini API did not respond within {GEMINI_TIMEOUT_SECONDS} seconds"
            )
        except Exception as e:
            logger.error("Error analyzing image with Gemini: %s", e, exc_info=True)
            raise

    async def chat_reply(
        self,
        prior_turns: list[dict[str, str]],
        user_message: str,
        memory_facts: list[str] | None = None,
    ) -> str:
        """
        Conversational reply using recent history + current user message (text only).
        prior_turns: [{"role": "user"|"assistant", "content": "..."}] excluding the current message.
        """
        user_message = (user_message or "").strip()
        if not user_message:
            return "Send me a message or a photo of the issue and I will help."

        lines = [CHAT_SYSTEM]
        if memory_facts:
            lines.extend(["", "Long-term facts about this customer:"])
            for fact in memory_facts[:10]:
                lines.append(f"- {fact}")
        lines.extend(["", "Conversation so far:"])
        for t in prior_turns[-20:]:
            role = t.get("role", "")
            content = (t.get("content") or "").strip()
            if not content:
                continue
            if len(content) > 500:
                content = content[:497] + "..."
            label = "User" if role == "user" else "Assistant"
            lines.append(f"{label}: {content}")
        lines.extend(["", f"User: {user_message}", "", "Assistant:"])
        prompt = "\n".join(lines)

        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.models.generate_content,
                    model=GEMINI_MODEL,
                    contents=prompt,
                ),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
            text = (response.text or "").strip()
            if len(text) > 1500:
                text = text[:1497] + "..."
            return text or "I am not sure how to answer that—try sending a photo of the issue."
        except asyncio.TimeoutError:
            logger.error("Gemini chat timed out after %ds", GEMINI_TIMEOUT_SECONDS)
            raise
        except Exception as e:
            logger.error("Gemini chat error: %s", e, exc_info=True)
            raise

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Gemini response into structured homeowner/pro sections.

        Returns:
            dict with 'homeowner_brief', 'pro_brief', 'severity', 'full_response'
        """
        try:
            parts = response_text.split("**PRO BRIEF:**")

            if len(parts) == 2:
                homeowner_section = parts[0].replace("**HOMEOWNER BRIEF:**", "").strip()
                pro_section = parts[1].strip()

                severity = "Medium"
                for line in pro_section.split("\n"):
                    if "severity" in line.lower():
                        if "high" in line.lower():
                            severity = "High"
                        elif "low" in line.lower():
                            severity = "Low"
                        break

                return {
                    "homeowner_brief": homeowner_section,
                    "pro_brief": pro_section,
                    "severity": severity,
                    "full_response": response_text,
                }
            else:
                logger.warning("Could not parse Gemini response into sections")
                return {
                    "homeowner_brief": response_text,
                    "pro_brief": "See full response above",
                    "severity": "Medium",
                    "full_response": response_text,
                }

        except Exception as e:
            logger.error("Error parsing Gemini response: %s", e)
            return {
                "homeowner_brief": response_text,
                "pro_brief": "Error parsing response",
                "severity": "Medium",
                "full_response": response_text,
            }


# Global service instance
gemini_service = GeminiService()
