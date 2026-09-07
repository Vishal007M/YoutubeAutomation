"""
trend_finder.py - Uses Gemini AI (google-genai SDK) to find unique trending kids topics.
Checks history to NEVER repeat a concept.
"""
import json
import random
import logging
from google import genai

logger = logging.getLogger(__name__)

KIDS_CATEGORIES = [
    "animals", "space and planets", "dinosaurs", "ocean creatures", "insects and bugs",
    "simple science experiments", "geography and countries", "history facts for kids",
    "fairy tales and myths", "riddles and brain teasers", "funny jokes",
    "food and cooking basics", "sports fun facts", "nature and plants",
    "weather and seasons", "colors and shapes", "numbers and math fun",
    "ABC and words", "superheroes origin", "robots and technology",
    "art and craft ideas", "music fun facts", "body and health for kids",
    "transportation and vehicles", "famous people for kids", "holidays and festivals",
    "environment and recycling", "underwater world", "birds", "reptiles",
    "magical creatures", "volcanoes and earthquakes", "rainforest animals",
    "polar animals", "farm animals", "wild cats", "dogs and puppies",
    "sharks and deep sea", "human body for kids", "how things are made",
    "world records for kids", "baby animals",
]

FALLBACK_TOPICS = [
    {"topic": "Why Do Cats Always Land on Their Feet?", "category": "animals",
     "emoji": "cat", "hook": "Cats have an amazing superpower - they almost never get hurt when they fall!",
     "color_scheme": ["#FF6B6B", "#FFE66D"]},
    {"topic": "How Big Is the Sun Compared to Earth?", "category": "space and planets",
     "emoji": "sun", "hook": "The Sun is SO big that one million Earths could fit inside it!",
     "color_scheme": ["#F7971E", "#FFD200"]},
    {"topic": "Amazing Facts About Blue Whales", "category": "ocean creatures",
     "emoji": "whale", "hook": "The blue whale is the largest animal that has EVER lived on Earth!",
     "color_scheme": ["#1A78C2", "#4ECDC4"]},
    {"topic": "Why Do We Dream When We Sleep?", "category": "human body for kids",
     "emoji": "moon", "hook": "Every night while you sleep your brain is having an adventure!",
     "color_scheme": ["#8E44AD", "#3498DB"]},
    {"topic": "How Do Bees Make Honey?", "category": "insects and bugs",
     "emoji": "bee", "hook": "Bees are natures tiny chefs and they make something delicious!",
     "color_scheme": ["#F39C12", "#27AE60"]},
]


def find_trending_topic(config, history):
    """Use Gemini to find a unique, engaging kids topic not in history."""
    client = genai.Client(api_key=config["gemini_api_key"])

    used_topics = history.get_used_topics(limit=150)
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "None yet"

    prompt = f"""You are a viral YouTube Shorts content expert for kids aged 3-10 years.

Pick ONE unique, super engaging topic for a kids educational short video.

Available categories: {", ".join(KIDS_CATEGORIES)}

Topics ALREADY USED - do NOT repeat or create anything similar:
{used_str}

Requirements:
- Must be 100% safe and G-rated for young children
- Pick a VERY SPECIFIC angle (not just "animals" but "Why do giraffes have long necks?")
- Should be fascinating, surprising, or funny for kids
- Completely different from all used topics above

Return ONLY raw valid JSON (no markdown, no triple backticks, no extra text):
{{
    "topic": "Why Do Giraffes Have Such Long Necks?",
    "category": "animals",
    "emoji": "giraffe",
    "hook": "Giraffes have necks as long as a whole school bus!",
    "color_scheme": ["#F9A825", "#2E7D32"]
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        topic_data = json.loads(text)
        logger.info(f"Gemini topic selected: {topic_data['topic']}")
        return topic_data

    except Exception as e:
        logger.warning(f"Gemini topic generation failed ({e}), using fallback")
        used_lower = {t.lower() for t in used_topics}
        unused = [t for t in FALLBACK_TOPICS if t["topic"].lower() not in used_lower]
        return random.choice(unused if unused else FALLBACK_TOPICS)
