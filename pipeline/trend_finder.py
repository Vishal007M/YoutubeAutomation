"""
trend_finder.py - Interactive & Automated Topic Selector for YouTube Shorts.
- Lets user interactively choose categories (Fairy Tales, Science Facts, Funny Stories, Riddles, ABC/Numbers)
- Lets user choose "Other" and type their own custom topic
- Supports fully automated random mode (guaranteeing different categories for Video 1 & Video 2)
- Zero mentions of "Part 1" or "Part 2"
"""
import sys
import json
import random
import logging
from google import genai

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "1": ("fairy tales", "🏰 Fairy Tales"),
    "2": ("science facts", "🔬 Science Facts"),
    "3": ("funny stories", "😂 Funny Stories"),
    "4": ("riddles", "🧩 Riddles"),
    "5": ("ABC/numbers", "🔤 ABC / Numbers"),
}

CORE_CATEGORIES = [
    "fairy tales",
    "science facts",
    "funny stories",
    "riddles",
    "ABC/numbers",
]

# Robust resilient models available on this API key
GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]


def _call_gemini_resilient(client, prompt: str) -> str:
    """Try models in sequence to prevent quota or 503 errors."""
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {model_name} note ({e}), trying next available...")
    raise RuntimeError("All Gemini models temporarily unavailable")


def _prompt_user_for_topic(video_num: int, exclude_cat: str = "") -> tuple[str, str]:
    """
    Prompt user in terminal for video choice:
    Returns (category, custom_text_or_empty)
    """
    default_cat = "random"
    print(f"\n👉 Choose topic for Video {video_num}:")
    print("   [1] 🏰 Fairy Tales")
    print("   [2] 🔬 Science Facts")
    print("   [3] 😂 Funny Stories")
    print("   [4] 🧩 Riddles")
    print("   [5] 🔤 ABC / Numbers")
    print("   [6] 🎲 Random (AI picks a fresh trending topic)")
    print("   [7] ✍️  Other / Custom (Type your own topic)")

    try:
        choice = input(f"   Enter choice [1-7, Default: 6]: ").strip()
    except Exception:
        choice = "6"

    if choice in CATEGORY_MAP:
        cat = CATEGORY_MAP[choice][0]
        return cat, ""
    elif choice == "7":
        try:
            custom = input(f"   📝 Type your custom topic for Video {video_num}: ").strip()
        except Exception:
            custom = ""
        if not custom:
            custom = "A magical playful baby animal adventure"
        return "custom", custom
    else:
        # Random selection
        pool = [c for c in CORE_CATEGORIES if c != exclude_cat] or CORE_CATEGORIES
        return random.choice(pool), ""


def _generate_topic_for_spec(client, category: str, custom_text: str, history) -> dict:
    """Generate or flesh out structured topic data using Gemini."""
    used_topics = history.get_used_topics(limit=150)
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "None yet"

    if category == "custom" and custom_text:
        prompt = f"""You are a professional children's TV producer for YouTube Shorts (ages 3-8).
A user requested this custom idea: "{custom_text}"

Turn this idea into a structured kids YouTube Short.
REQUIREMENTS:
- topic: Catchy, fun title (max 50 chars, NO 'Part 1' or 'Part 2')
- category: Closest category (fairy tales, science facts, funny stories, riddles, or kids fun)
- subject: Single noun for 3D cartoon mascot (e.g. puppy, dragon, monkey, squirrel, sun, rocket, dinosaur)
- hook: Exciting 1-sentence hook to grab kids' attention
- video_query: Stock video search query (e.g. "playful puppy grass")
- veo_prompt: 3D Pixar/Disney style video prompt (vertical 9:16)
- color_scheme: Two vibrant hex colors

Return ONLY raw valid JSON:
{{
  "topic": "The Squirrel Who Built a Rocket",
  "category": "fairy tales",
  "subject": "squirrel",
  "hook": "Meet Sammy, a brave little squirrel who built a rocket out of an acorn!",
  "video_query": "cute funny squirrel tree",
  "veo_prompt": "A cute 3D cartoon baby squirrel wearing a tiny space helmet, Disney Pixar style, vertical 9:16",
  "color_scheme": ["#FF5E62", "#FF9966"]
}}"""
    else:
        prompt = f"""You are a viral YouTube Shorts researcher and children's animator (ages 3-8).
The creator has chosen the category: {category.upper()}

Find the MOST VIRAL, TRENDING, and FASCINATING kids concept for this category right now!
Focus on high-retention, high-curiosity angles that blow kids' minds and get millions of views on YouTube Shorts:
- If Fairy Tales: Classic magical characters (dragon, fairy, magic carpet, wizard puppy, friendly giant) with a sweet or funny twist!
- If Science Facts: Mind-blowing, weird, colorful nature or animal superpowers!
- If Funny Stories: Clumsy cute animals in goofy situations with a hilarious punchline!
- If Riddles: Catchy rhyming mystery question that kids can't resist trying to guess!
- If ABC/numbers: Fast energetic counting countdowns, magic shapes, or mystery rhyming words!

TOPICS ALREADY USED (NEVER repeat or make similar):
{used_str}

REQUIREMENTS:
- Safe, 100% G-rated, fun, exciting.
- NO mentions of 'Part 1' or 'Part 2'.
- topic: Catchy, viral title (max 50 chars)
- category: "{category}"
- subject: Single noun for 3D cartoon mascot (e.g. monkey, dragon, fairy, fish, lion, rabbit, sun, robot, bee, car, dinosaur, flamingo)
- hook: Irresistible 1-sentence curiosity hook that grabs kids instantly!
- video_query: High-impact search query for background video.
- veo_prompt: 3D cartoon Pixar/Disney style prompt (vertical 9:16).
- color_scheme: Two vibrant hex colors.

Return ONLY raw valid JSON:
{{
  "topic": "Why Do Whales Sing Underwater?",
  "category": "{category}",
  "subject": "whale",
  "hook": "Did you know giant whales sing secret songs across entire oceans?",
  "video_query": "blue whale swimming ocean underwater",
  "veo_prompt": "A majestic friendly 3D cartoon blue whale swimming in sunny blue ocean, Pixar Disney style, vertical 9:16",
  "color_scheme": ["#1A78C2", "#4ECDC4"]
}}"""

    text = _call_gemini_resilient(client, prompt)

    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    if "subject" not in data or not data["subject"]:
        data["subject"] = data.get("topic", "star").split()[0].lower()

    return data


def select_topics_for_run(config, history) -> tuple[dict, dict]:
    """
    Selects or prompts user for Video 1 and Video 2 topics.
    Returns: (topic1_data, topic2_data)
    """
    client = genai.Client(api_key=config["gemini_api_key"])

    # Check if running interactively
    is_interactive = sys.stdin.isatty()

    if is_interactive:
        print("\n" + "═" * 60)
        print("   🎬  CHOOSE YOUR TOPICS FOR TODAY'S 2 SHORTS")
        print("═" * 60)
        cat1, custom1 = _prompt_user_for_topic(1)
        cat2, custom2 = _prompt_user_for_topic(2, exclude_cat=cat1 if cat1 != "custom" else "")
    else:
        # Automated non-interactive mode: pick 2 different random categories
        cat1 = random.choice(CORE_CATEGORIES)
        cat2 = random.choice([c for c in CORE_CATEGORIES if c != cat1])
        custom1, custom2 = "", ""

    print(f"\n✨ Generating creative concepts with Gemini AI…")
    t1 = _generate_topic_for_spec(client, cat1, custom1, history)
    t2 = _generate_topic_for_spec(client, cat2, custom2, history)

    logger.info(f"Video 1 topic: '{t1['topic']}' ({t1['category']})")
    logger.info(f"Video 2 topic: '{t2['topic']}' ({t2['category']})")

    return t1, t2


# Backwards compatibility aliases
def find_two_different_topics(config, history):
    return select_topics_for_run(config, history)


def find_trending_topic(config, history):
    t1, _ = select_topics_for_run(config, history)
    return t1
