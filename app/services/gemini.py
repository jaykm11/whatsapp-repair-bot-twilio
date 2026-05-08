"""
Gemini AI Service
Multimodal image analysis using Google's Gemini 1.5 Pro
"""

import logging
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for analyzing household issues using Gemini AI"""

    def __init__(self):
        """Initialize Gemini model"""
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-3.1-pro-preview")

        # Master persona prompt for household repairs
        self.system_prompt = """You are a Master Plumber and HVAC Technician with 25+ years of experience diagnosing household issues.

You specialize in identifying plumbing problems (leaks, clogs, pipe damage, water heaters, fixtures) and HVAC issues (heating, cooling, ventilation, ductwork, thermostats).

When analyzing an image, provide TWO distinct responses:

1. HOMEOWNER BRIEF:
   - Simple, non-technical explanation (2-3 sentences)
   - What the issue is in plain English
   - Immediate safety concerns if any
   - Whether they should stop using the system

2. PRO BRIEF:
   - Issue identification (specific component/system)
   - Severity level: Low / Medium / High
   - Recommended parts/tools needed
   - Estimated repair time
   - Safety considerations for the technician
   - Any additional diagnostic steps needed

Format your response exactly as follows:

**HOMEOWNER BRIEF:**
[Your homeowner explanation here]

**PRO BRIEF:**
- **Issue:** [Specific problem]
- **Severity:** [Low/Medium/High]
- **Parts Needed:** [List of parts]
- **Tools Required:** [List of tools]
- **Estimated Time:** [Time estimate]
- **Safety Notes:** [Safety information]
- **Next Steps:** [Additional diagnostics if needed]

If the image doesn't show a plumbing or HVAC issue, politely explain that you can only diagnose household repair issues.
"""

    async def analyze_image(self, image_bytes: bytes, user_message: str = "") -> dict:
        """
        Analyze a household issue from an image

        Args:
            image_bytes: Image data as bytes
            user_message: Optional text message from user describing the issue

        Returns:
            dict with 'homeowner_brief' and 'pro_brief' keys
        """
        try:
            logger.info("Analyzing image with Gemini AI")

            # Construct the full prompt
            user_context = f"\nUser's description: {user_message}" if user_message else ""
            full_prompt = f"{self.system_prompt}{user_context}\n\nAnalyze the image and provide your diagnosis:"

            # Prepare the image for Gemini
            image_part = {
                "mime_type": "image/jpeg",  # Assuming JPEG, can be made dynamic
                "data": image_bytes
            }

            # Generate response
            response = self.model.generate_content([full_prompt, image_part])

            logger.info("Gemini analysis completed successfully")

            # Parse the response into homeowner and pro sections
            full_response = response.text
            parsed_response = self._parse_response(full_response)

            return parsed_response

        except Exception as e:
            logger.error(f"Error analyzing image with Gemini: {e}", exc_info=True)
            raise

    def _parse_response(self, response_text: str) -> dict:
        """
        Parse Gemini response into structured format

        Args:
            response_text: Full text response from Gemini

        Returns:
            dict with 'homeowner_brief', 'pro_brief', 'severity', and 'full_response'
        """
        try:
            # Split on the headers
            parts = response_text.split("**PRO BRIEF:**")

            if len(parts) == 2:
                homeowner_section = parts[0].replace("**HOMEOWNER BRIEF:**", "").strip()
                pro_section = parts[1].strip()

                # Extract severity from pro section
                severity = "Medium"  # Default
                if "Severity:" in pro_section or "**Severity:**" in pro_section:
                    for line in pro_section.split('\n'):
                        if 'severity' in line.lower():
                            if 'high' in line.lower():
                                severity = "High"
                            elif 'low' in line.lower():
                                severity = "Low"
                            elif 'medium' in line.lower():
                                severity = "Medium"
                            break

                return {
                    "homeowner_brief": homeowner_section,
                    "pro_brief": pro_section,
                    "severity": severity,
                    "full_response": response_text
                }
            else:
                # If parsing fails, return the whole response
                logger.warning("Could not parse Gemini response into sections")
                return {
                    "homeowner_brief": response_text,
                    "pro_brief": "See full response above",
                    "severity": "Medium",
                    "full_response": response_text
                }

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                "homeowner_brief": response_text,
                "pro_brief": "Error parsing response",
                "severity": "Medium",
                "full_response": response_text
            }


# Global service instance
gemini_service = GeminiService()
