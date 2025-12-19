"""
Timeline Image Generator Service

Generates beautiful infographic timeline images using Gemini 3 Pro Image Generation.
Creates visual summaries of a child's developmental journey.

🌟 Wu Wei: This service creates artifacts, it doesn't diagnose or assess.
"""

import os
import base64
import mimetypes
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class TimelineImageService:
    """
    Generates timeline infographic images using Gemini 3 Pro.

    Creates visual representations of a child's journey through Chitta,
    showing key moments, milestones, and observations.
    """

    def __init__(self):
        """Initialize the timeline image service."""
        self.client = None
        self.model = "gemini-3-pro-image-preview"  # Gemini 3 Pro image generation
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set - timeline generation will not work")
            return

        try:
            self.client = genai.Client(api_key=api_key)
            logger.info("Gemini client initialized for timeline generation")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")

    def _build_timeline_prompt(
        self,
        child_name: str,
        events: List[Dict[str, Any]],
        style: str = "warm"
    ) -> str:
        """
        Build a detailed prompt for timeline infographic generation.

        Uses Gemini 3 Pro prompting best practices:
        - Subject: Who/what is in the image
        - Composition: How it's framed
        - Style: Overall aesthetic
        - Text integration: Clear text specifications
        - Format: Aspect ratio and resolution

        Args:
            child_name: Name of the child
            events: List of timeline events with dates and descriptions
            style: Visual style (warm, professional, playful)

        Returns:
            Detailed prompt string for image generation
        """
        # Format events into structured list
        events_text = "\n".join([
            f"{i+1}. {event.get('date', '')}: {event.get('title', '')} ({event.get('description', '')})"
            for i, event in enumerate(events)
        ])

        style_configs = {
            "warm": {
                "palette": "soft pastel purple (#8B5CF6), warm amber (#F59E0B), cream background (#FFF8F0)",
                "aesthetic": "warm, friendly watercolor illustration style with soft rounded shapes",
                "mood": "nurturing and encouraging"
            },
            "professional": {
                "palette": "clean blue (#3B82F6), slate gray (#64748B), white background",
                "aesthetic": "modern minimalist infographic style with clean geometric shapes",
                "mood": "professional and trustworthy"
            },
            "playful": {
                "palette": "bright teal (#14B8A6), sunny yellow (#FBBF24), soft pink (#F472B6), light background",
                "aesthetic": "playful cartoon illustration style with bouncy rounded elements",
                "mood": "joyful and celebratory"
            }
        }

        config = style_configs.get(style, style_configs["warm"])

        prompt = f"""Create a developmental progress timeline infographic for a child named "{child_name}".

CONCEPT: A timeline showing REAL PROGRESS over time - how the child has grown and developed across weeks/months.
Parents should see concrete changes: "First video: 2 sec eye contact → Third video: 8 sec eye contact"
This celebrates growth and gives hope.

SUBJECT: A vertical timeline infographic showing "{child_name}"'s developmental progress over time.

COMPOSITION: 9:16 vertical portrait format for mobile. Timeline flows top to bottom chronologically.

STYLE: {config['aesthetic']}. Color palette: {config['palette']}. Overall mood: {config['mood']}.

HEADER (Hebrew, RTL):
"ההתפתחות של {child_name}" - large, warm font
Small date range below: "ספטמבר - נובמבר 2024"

TIMELINE EVENTS ({len(events)} milestones):
{events_text}

VISUAL DESIGN:
- Clear vertical timeline with DATE markers on the left side (like "15.09", "02.10")
- Each event is a card/bubble connected to the timeline
- Use emoji icons as colorful markers for each event type
- Show PROGRESS visually - maybe small graphs, arrows, or growth indicators
- Breakthrough moments (💫) should stand out more
- Color-code by category: observations (blue), milestones (gold), breakthroughs (purple)

FOOTER (Hebrew):
"כל צעד קטן הוא הישג גדול 💙"

CRITICAL REQUIREMENTS:
- Hebrew text MUST be crisp, readable, and RIGHT-TO-LEFT aligned
- Dates should be clearly visible on the timeline
- Show the PASSAGE OF TIME clearly - this is a journey over weeks
- Font size large enough for mobile (minimum 14pt)
- High contrast for accessibility
- Parents should feel PROUD seeing their child's progress

Generate a beautiful, shareable timeline that shows real developmental growth."""

        return prompt

    async def generate_timeline_image(
        self,
        child_name: str,
        events: List[Dict[str, Any]],
        family_id: str,
        style: str = "warm"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a timeline infographic image.

        Args:
            child_name: Name of the child
            events: List of timeline events
            family_id: Family ID for file storage
            style: Visual style preference

        Returns:
            Dict with image_path, image_url, and metadata, or None on failure
        """
        if not self.client:
            logger.error("Gemini client not initialized")
            return None

        if not events:
            logger.warning("No events provided for timeline")
            return None

        prompt = self._build_timeline_prompt(child_name, events, style)

        try:
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]

            generate_content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    image_size="1K",  # High quality for infographics
                ),
            )

            # Generate the image
            logger.info(f"Generating timeline image for {child_name} with {len(events)} events")

            image_data = None
            mime_type = None

            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                part = chunk.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    image_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    break

            if not image_data:
                logger.error("No image data received from Gemini")
                return None

            # Save the image
            uploads_dir = Path("uploads") / family_id / "timelines"
            uploads_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = mimetypes.guess_extension(mime_type) or ".png"
            file_name = f"timeline_{timestamp}{file_extension}"
            file_path = uploads_dir / file_name

            with open(file_path, "wb") as f:
                f.write(image_data)

            logger.info(f"Timeline image saved to: {file_path}")

            # Return result - use full backend URL for image
            backend_url = os.environ.get("BACKEND_URL", "http://localhost:8000")
            return {
                "image_path": str(file_path),
                "image_url": f"{backend_url}/uploads/{family_id}/timelines/{file_name}",
                "mime_type": mime_type,
                "generated_at": datetime.now().isoformat(),
                "child_name": child_name,
                "event_count": len(events),
                "style": style
            }

        except Exception as e:
            logger.error(f"Error generating timeline image: {e}")
            return None

    def _format_date(self, date_value) -> str:
        """Convert various date formats to display string."""
        if not date_value:
            return "היום"
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        if isinstance(date_value, str) and len(date_value) >= 10:
            return date_value[:10]
        return "היום"

    def build_events_from_family_state(
        self,
        family_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build developmental timeline events from legacy session data.
        Kept for backward compatibility.
        """
        extracted = family_state.get("extracted_data", {})
        if not isinstance(extracted, dict):
            extracted = {}

        child_name = extracted.get("child_name", "דניאל")
        return self._build_mock_events(child_name)

    def build_events_from_gestalt(
        self,
        gestalt_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Build timeline events from Living Gestalt data.

        Uses:
        - stories: Main source of timeline events
        - journal: Session summaries
        - facts: Key discoveries about the child

        Args:
            gestalt_data: The gestalt data from data/children/{family_id}.json

        Returns:
            List of timeline events
        """
        child_name = gestalt_data.get("name", "הילד/ה")
        events = []

        # Domain to icon/category mapping
        domain_icons = {
            "behavioral": ("🎯", "behavior"),
            "emotional": ("💗", "emotional"),
            "social": ("👫", "social"),
            "motor": ("🏃", "motor"),
            "cognitive": ("🧠", "cognitive"),
            "language": ("💬", "language"),
            "sensory": ("👁️", "sensory"),
            "strengths": ("⭐", "strength"),
            "family": ("👨‍👩‍👧", "family"),
            "identity": ("🎈", "identity"),
        }

        # 1. Build events from stories (main source)
        stories = gestalt_data.get("stories", [])
        for story in stories:
            timestamp = story.get("timestamp", "")
            if isinstance(timestamp, str) and len(timestamp) >= 10:
                date_str = timestamp[5:10].replace("-", ".")  # MM.DD format
            else:
                date_str = "היום"

            domains = story.get("domains", [])
            primary_domain = domains[0] if domains else "general"
            icon, category = domain_icons.get(primary_domain, ("📝", "general"))

            # Build title from reveals
            reveals = story.get("reveals", [])
            title = reveals[0] if reveals else "רגע חשוב"

            events.append({
                "date": date_str,
                "title": title,
                "description": story.get("summary", ""),
                "icon": icon,
                "category": category
            })

        # 2. Add key facts as events (filtered to significant ones)
        understanding = gestalt_data.get("understanding", {})
        facts = understanding.get("facts", []) if understanding else []
        for fact in facts:
            # Only include high-confidence facts about strengths or identity
            if fact.get("domain") in ["strengths", "identity"] and fact.get("confidence", 0) >= 0.9:
                timestamp = fact.get("t_created", "")
                if isinstance(timestamp, str) and len(timestamp) >= 10:
                    date_str = timestamp[5:10].replace("-", ".")
                else:
                    date_str = "היום"

                domain = fact.get("domain", "general")
                icon, category = domain_icons.get(domain, ("✨", "discovery"))

                events.append({
                    "date": date_str,
                    "title": "גילוי חדש" if domain == "strengths" else "הכרנו",
                    "description": fact.get("content", ""),
                    "icon": icon,
                    "category": category
                })

        # 3. Add journal entries for notable moments
        journal = gestalt_data.get("journal", [])
        for entry in journal:
            if entry.get("significance") in ["notable", "breakthrough"]:
                timestamp = entry.get("timestamp", "")
                if isinstance(timestamp, str) and len(timestamp) >= 10:
                    date_str = timestamp[5:10].replace("-", ".")
                else:
                    date_str = "היום"

                learned = entry.get("learned", [])
                title = "התקדמות!" if entry.get("significance") == "breakthrough" else "שיחה חשובה"

                events.append({
                    "date": date_str,
                    "title": title,
                    "description": entry.get("summary", "") + (f" ({', '.join(learned[:2])})" if learned else ""),
                    "icon": "🌟" if entry.get("significance") == "breakthrough" else "💭",
                    "category": "milestone" if entry.get("significance") == "breakthrough" else "session"
                })

        # If no real events, return mock data
        if not events:
            return self._build_mock_events(child_name)

        # Sort by date and limit
        events.sort(key=lambda e: e.get("date", ""))
        return events[:10]  # Limit to 10 events for the infographic

    def _build_mock_events(self, child_name: str) -> List[Dict[str, Any]]:
        """Build mock timeline events for demo purposes."""
        return [
            {
                "date": "15.09",
                "title": "הכרנו!",
                "description": f"{child_name} אוהב רכבות ובננות",
                "icon": "🚂",
                "category": "start"
            },
            {
                "date": "20.09",
                "title": "גילוי חדש",
                "description": "מזהה את כל החיות בספר!",
                "icon": "🦁",
                "category": "discovery"
            },
            {
                "date": "28.09",
                "title": "רגע מצחיק",
                "description": f"{child_name} שם סיר על הראש ואמר 'כובע'",
                "icon": "😂",
                "category": "funny"
            },
            {
                "date": "05.10",
                "title": "אוהב מוזיקה",
                "description": "רוקד כשיש שיר של עידן רייכל",
                "icon": "🎵",
                "category": "preference"
            },
            {
                "date": "12.10",
                "title": "חבר חדש",
                "description": "שיחק עם יותם בגן לראשונה",
                "icon": "👫",
                "category": "social"
            },
            {
                "date": "18.10",
                "title": "משפט ראשון!",
                "description": "'אמא בואי' - שני מילים ביחד",
                "icon": "💬",
                "category": "language"
            },
            {
                "date": "25.10",
                "title": "עצמאות",
                "description": "לבש נעליים לבד (על הרגל הלא נכונה)",
                "icon": "👟",
                "category": "independence"
            },
            {
                "date": "01.11",
                "title": "הפתעה",
                "description": f"{child_name} הביא לאמא פרח מהגינה",
                "icon": "🌸",
                "category": "sweet"
            },
        ]


# Singleton instance
_timeline_service: Optional[TimelineImageService] = None


def get_timeline_service() -> TimelineImageService:
    """Get or create the timeline image service singleton."""
    global _timeline_service
    if _timeline_service is None:
        _timeline_service = TimelineImageService()
    return _timeline_service
