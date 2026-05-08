"""
Professional Matching Service
Recommends appropriate professionals based on issue severity and type
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Literal

logger = logging.getLogger(__name__)

# Load professionals database
PROFESSIONALS_FILE = Path(__file__).parent.parent.parent / "professionals.json"

def load_professionals() -> Dict:
    """Load professionals from JSON file"""
    try:
        with open(PROFESSIONALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load professionals.json: {e}")
        return {}


def get_profession_type(issue_description: str) -> str:
    """
    Determine profession type from issue description

    Args:
        issue_description: The AI-generated diagnosis text

    Returns:
        Profession category: "plumbers", "hvac", "electricians", or "handyman"
    """
    issue_lower = issue_description.lower()

    # Plumbing keywords
    if any(word in issue_lower for word in [
        'pipe', 'plumb', 'leak', 'drain', 'toilet', 'faucet',
        'sink', 'water', 'sewer', 'valve', 'fixture'
    ]):
        return "plumbers"

    # HVAC keywords
    if any(word in issue_lower for word in [
        'hvac', 'ac', 'air condition', 'heat', 'cooling', 'furnace',
        'thermostat', 'duct', 'vent', 'compressor', 'refrigerant'
    ]):
        return "hvac"

    # Electrical keywords
    if any(word in issue_lower for word in [
        'electric', 'wiring', 'outlet', 'switch', 'circuit', 'breaker',
        'light', 'power', 'voltage', 'electrical'
    ]):
        return "electricians"

    # Default to handyman for general issues
    return "handyman"


def recommend_professionals(
    profession_type: str,
    severity: Literal["Low", "Medium", "High"],
    max_recommendations: int = 3
) -> List[Dict]:
    """
    Recommend professionals based on issue type and severity

    Args:
        profession_type: Category of professional needed
        severity: Urgency level from AI diagnosis
        max_recommendations: Maximum number of recommendations

    Returns:
        List of recommended professionals with reasoning
    """
    professionals_db = load_professionals()

    if profession_type not in professionals_db:
        logger.warning(f"Unknown profession type: {profession_type}")
        return []

    all_pros = professionals_db[profession_type]

    # Sort by urgency and severity
    if severity == "High":
        # High severity: prioritize immediate availability, then rating
        sorted_pros = sorted(
            all_pros,
            key=lambda p: (
                0 if "24/7" in p["availability"] or "Same Day" in p["availability"] else 1,
                -p["rating"]
            )
        )
        urgency_note = "⚠️ **HIGH URGENCY** - Showing fastest response options first"

    elif severity == "Medium":
        # Medium: balance of speed and cost
        sorted_pros = sorted(
            all_pros,
            key=lambda p: (
                0 if "Same Day" in p["availability"] or "Next Day" in p["availability"] else 1,
                -p["rating"],
                int(p["hourly_rate"].split('-')[0].replace('$', ''))  # Sort by base rate
            )
        )
        urgency_note = "🔧 **MODERATE URGENCY** - Showing balanced cost/speed options"

    else:  # Low severity
        # Low: prioritize cost, then rating
        sorted_pros = sorted(
            all_pros,
            key=lambda p: (
                int(p["hourly_rate"].split('-')[0].replace('$', '')),  # Cheapest first
                -p["rating"]
            )
        )
        urgency_note = "💰 **LOW URGENCY** - Showing most cost-effective options"

    # Take top recommendations
    recommendations = sorted_pros[:max_recommendations]

    # Add recommendation reasoning
    for i, pro in enumerate(recommendations):
        if i == 0:
            if severity == "High":
                pro["why_recommended"] = "Fastest response time"
            elif severity == "Medium":
                pro["why_recommended"] = "Best balance of speed and quality"
            else:
                pro["why_recommended"] = "Most affordable option"
        elif i == 1:
            if severity == "High":
                pro["why_recommended"] = "Backup option - also very fast"
            else:
                pro["why_recommended"] = "Good alternative option"
        else:
            pro["why_recommended"] = "Additional option for comparison"

    return recommendations, urgency_note


def format_professional_recommendations(
    recommendations: List[Dict],
    urgency_note: str
) -> str:
    """
    Format professional recommendations as WhatsApp message

    Args:
        recommendations: List of recommended professionals
        urgency_note: Note about urgency level

    Returns:
        Formatted string for WhatsApp
    """
    if not recommendations:
        return "\n\n⚠️ No professionals found for this issue type."

    output = f"\n\n---\n\n{urgency_note}\n\n🔧 **Recommended Professionals:**\n\n"

    for i, pro in enumerate(recommendations, 1):
        output += f"**{i}. {pro['name']}** ⭐ {pro['rating']}★\n"
        output += f"   📞 {pro['phone']}\n"
        output += f"   💵 {pro['hourly_rate']}\n"
        output += f"   ⏰ Availability: {pro['availability']}\n"
        output += f"   📜 Credentials: {', '.join(pro['certifications'])}\n"
        output += f"   🏘️ Serves: {', '.join(pro['areas'])}\n"

        if pro.get("emergency_fee") and pro["emergency_fee"] != "N/A":
            output += f"   ⚡ Emergency Fee: {pro['emergency_fee']}\n"

        output += f"\n   ✅ **Pros:** {', '.join(pro['pros'])}\n"
        output += f"   ❌ **Cons:** {', '.join(pro['cons'])}\n"
        output += f"   💡 *Why recommended:* {pro['why_recommended']}\n\n"

    return output
