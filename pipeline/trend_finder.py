"""
trend_finder.py - Uses Gemini AI to discover unique trending kids topics.
Checks history to NEVER repeat a concept.
Generates full visual metadata (subject, video queries, 3D character name).
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
    {
        "topic": "Why Do Cats Always Land on Their Feet?",
        "category": "animals",
        "subject": "cat",
        "hook": "Cats have an amazing superpower - they almost never get hurt when they fall!",
        "video_query": "cute kitten playful jumping",
        "veo_prompt": "A cute 3D Pixar style playful kitten landing gracefully on fluffy grass, bright colors, vertical 9:16",
        "color_scheme": ["#FF6B6B", "#FFE66D"]
    },
    {
        "topic": "How Big Is the Sun Compared to Earth?",
        "category": "space and planets",
        "subject": "sun",
        "hook": "The Sun is SO big that one million Earths could fit inside it!",
        "video_query": "sun space solar system earth",
        "veo_prompt": "A glowing friendly 3D cartoon smiling sun in deep blue outer space with stars, vertical 9:16",
        "color_scheme": ["#F7971E", "#FFD200"]
    },
    {
        "topic": "Amazing Facts About Blue Whales",
        "category": "ocean creatures",
        "subject": "whale",
        "hook": "The blue whale is the largest animal that has EVER lived on Earth!",
        "video_query": "blue whale ocean swimming underwater",
        "veo_prompt": "A majestic friendly 3D cartoon blue whale swimming peacefully in sunny blue ocean, vertical 9:16",
        "color_scheme": ["#1A78C2", "#4ECDC4"]
    },
    {
        "topic": "How Do Bees Make Honey?",
        "category": "insects and bugs",
        "subject": "honeybee",
        "hook": "Bees are nature's tiny chefs and they make something super sweet and delicious!",
        "video_query": "honey bee flowers colorful garden",
        "veo_prompt": "A cute fluffy 3D cartoon bumblebee flying around vibrant flowers in a sunny garden, vertical 9:16",
        "color_scheme": ["#F39C12", "#27AE60"]
    }
]


def find_trending_topic(config, history):
    """Use Gemini to find a unique, engaging kids topic not in history."""
    client = genai.Client(api_key=config["gemini_api_key"])

    used_topics = history.get_used_topics(limit=150)
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "None yet"

    prompt = f"""You are a viral YouTube Shorts creator making educational content for kids aged 3-10.

Pick ONE fascinating, specific topic for a kid-friendly educational short.

Categories: {", ".join(KIDS_CATEGORIES)}

Topics ALREADY USED (NEVER repeat or do anything similar):
{used_str}

Requirements:
- 100% G-rated, safe, fun, and curious for kids
- Must identify the specific core SUBJECT (single noun like octopus, giraffe, elephant, dinosaur, rocket, volcano, tiger, panda)
- Provide a search query for stock video (e.g. "cute playful elephant safari")
- Provide a 3D cartoon visual prompt for video generation
- Completely fresh and novel!

Return ONLY valid raw JSON without markdown or code fences:
{{
    "topic": "Why Do Giraffes Have Such Long Necks?",
    "category": "animals",
    "subject": "giraffe",
    "hook": "Giraffes have necks as long as an entire school bus!",
    "video_query": "giraffe savannah wildlife nature",
    "veo_prompt": "A charming cute 3D cartoon baby giraffe nibbling acacia tree leaves in a sunny African savannah, Disney Pixar style, vertical 9:16",
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
        # Ensure subject exists
        if "subject" not in topic_data or not topic_data["subject"]:
            topic_data["subject"] = topic_data.get("topic", "star").split()[0].lower()

        logger.info(f"Gemini topic selected: {topic_data['topic']} (Subject: {topic_data['subject']})")
        return topic_data

    except Exception as e:
        logger.warning(f"Gemini topic selection failed ({e}), using fallback")
        used_lower = {t.lower() for t in used_topics}
        unused = [t for t in FALLBACK_TOPICS if t["topic"].lower() not in used_lower]
        return random.choice(unused if unused else FALLBACK_TOPICS)
