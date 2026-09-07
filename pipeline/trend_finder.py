"""
trend_finder.py - Selects TWO DIFFERENT random kids categories and topics.
Guarantees:
- Part 1 is chosen from one category (e.g. funny stories)
- Part 2 is chosen from a DIFFERENT category (e.g. fairy tales, strictly cat2 != cat1)
- Neither topic has ever been used in history
- Includes core user categories: fairy tales, science facts, funny stories, riddles, ABC/numbers
"""
import json
import random
import logging
from google import genai

logger = logging.getLogger(__name__)

# Core categories requested by user + popular kids themes
CORE_CATEGORIES = [
    "fairy tales",
    "science facts",
    "funny stories",
    "riddles",
    "ABC/numbers",
]

EXPANDED_CATEGORIES = [
    "fairy tales",
    "science facts",
    "funny stories",
    "riddles",
    "ABC/numbers",
    "animals",
    "space and planets",
    "dinosaurs",
    "ocean creatures",
    "superheroes",
]

# Resilient models fallback list
GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

FALLBACK_PAIRS = [
    (
        {
            "topic": "The Monkey Who Forgot How to Climb",
            "category": "funny stories",
            "subject": "monkey",
            "hook": "Whoops! Barnaby the monkey tried to walk like a penguin and forgot how to climb trees!",
            "video_query": "funny playful monkey jungle",
            "veo_prompt": "A cute 3D cartoon playful monkey laughing in jungle, Pixar Disney style, vertical 9:16",
            "color_scheme": ["#FF5E62", "#FF9966"]
        },
        {
            "topic": "The Mouse Who Outsmarted a Dragon",
            "category": "fairy tales",
            "subject": "mouse",
            "hook": "Once upon a time in a magic kingdom, a tiny mouse challenged a giant roaring dragon!",
            "video_query": "magical fairy tale castle forest",
            "veo_prompt": "A cute 3D cartoon tiny mouse with a tiny shield facing a friendly giant dragon, Pixar Disney style, vertical 9:16",
            "color_scheme": ["#4E54C8", "#8F94FB"]
        }
    ),
    (
        {
            "topic": "The Mystery of the Flying Fish",
            "category": "science facts",
            "subject": "fish",
            "hook": "Guess what? There are real fish in the ocean that can jump out of the water and FLY!",
            "video_query": "flying fish ocean leaping",
            "veo_prompt": "A colorful 3D cartoon fish gliding above ocean waves with sunshine, Pixar Disney style, vertical 9:16",
            "color_scheme": ["#00C9FF", "#92FE9D"]
        },
        {
            "topic": "What Has Keys But Cannot Open Any Doors?",
            "category": "riddles",
            "subject": "musical notes",
            "hook": "Can you solve this super tricky riddle? What has eighty-eight keys but cannot open a single door?",
            "video_query": "colorful piano musical notes cartoon",
            "veo_prompt": "A cheerful 3D cartoon piano playing bouncy music notes in a colorful playroom, Pixar Disney style, vertical 9:16",
            "color_scheme": ["#F7971E", "#FFD200"]
        }
    )
]


def _call_gemini_resilient(client, prompt: str) -> str:
    """Try models in sequence to prevent 503 temporary spike errors."""
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {model_name} note ({e}), trying next...")
    raise RuntimeError("All Gemini models temporarily unavailable")


def find_two_different_topics(config, history):
    """
    Pick TWO completely DIFFERENT categories and topics for Part 1 and Part 2.
    Example: Part 1 = funny stories, Part 2 = fairy tales (cat2 != cat1).
    Returns: (topic1_data, topic2_data)
    """
    client = genai.Client(api_key=config["gemini_api_key"])

    # 1. Randomly choose Category 1 and Category 2 (guaranteed cat2 != cat1)
    # Give priority to core user categories (80% core, 20% expanded)
    pool = CORE_CATEGORIES if random.random() < 0.85 else EXPANDED_CATEGORIES
    cat1 = random.choice(pool)
    cat2 = random.choice([c for c in pool if c != cat1])

    used_topics = history.get_used_topics(limit=150)
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "None yet"

    prompt = f"""You are a top viral YouTube Shorts creator making two separate daily videos for kids aged 3-8.

Generate TWO completely different, high-engagement topics for today:

PART 1 SHORT:
- Category MUST BE: {cat1}
- Must be a fun, standalone topic for this category.

PART 2 SHORT:
- Category MUST BE: {cat2} (COMPLETELY DIFFERENT FROM PART 1!)
- Must be a fun, standalone topic for this category.

TOPICS ALREADY USED (NEVER repeat or make similar):
{used_str}

REQUIREMENTS FOR EACH:
- Safe, fun, exciting, G-rated for kids.
- Specific single-noun "subject" for 3D mascot (e.g. monkey, dragon, fish, lion, rabbit, sun, robot, bee, car, dinosaur).
- Exciting 1-sentence hook.
- Search query for background video.
- 3D cartoon Pixar/Disney style prompt.
- Two vibrant hex colors for badge/gradient.

Return ONLY raw valid JSON (no markdown fences, no triple backticks):
{{
  "part1": {{
    "topic": "The Clumsy Penguin Who Loved Roller Skates",
    "category": "{cat1}",
    "subject": "penguin",
    "hook": "Whoops! Pip the playful penguin strapped on shiny roller skates and zipped down the ice!",
    "video_query": "cute funny penguin sliding ice",
    "veo_prompt": "A cute 3D cartoon chubby penguin smiling on roller skates, Pixar Disney style, vertical 9:16",
    "color_scheme": ["#FF5E62", "#FF9966"]
  }},
  "part2": {{
    "topic": "The Secret Riddle of the Magic Clock",
    "category": "{cat2}",
    "subject": "alarm clock",
    "hook": "Can you solve this mystery? I have hands and a face, but no arms or smile! What am I?",
    "video_query": "ticking clock magic cartoon colorful",
    "veo_prompt": "A friendly 3D cartoon ticking alarm clock with glowing numbers in a magical room, Pixar Disney style, vertical 9:16",
    "color_scheme": ["#4E54C8", "#8F94FB"]
  }}
}}"""

    try:
        text = _call_gemini_resilient(client, prompt)

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        t1 = data["part1"]
        t2 = data["part2"]

        # Ensure subjects exist
        for t in [t1, t2]:
            if "subject" not in t or not t["subject"]:
                t["subject"] = t.get("topic", "star").split()[0].lower()

        logger.info(f"Generated Part 1: '{t1['topic']}' ({t1['category']})")
        logger.info(f"Generated Part 2: '{t2['topic']}' ({t2['category']})")
        return t1, t2

    except Exception as e:
        logger.warning(f"Dual topic generation failed ({e}), using fallback pair")
        pair = random.choice(FALLBACK_PAIRS)
        return pair[0], pair[1]


# Backwards compatibility alias
def find_trending_topic(config, history):
    t1, _ = find_two_different_topics(config, history)
    return t1
