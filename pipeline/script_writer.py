"""
script_writer.py - Generates highly engaging, standalone scripts for Part 1 and Part 2.
Each script is completely tailored to its specific topic and category
(fairy tales, science facts, funny stories, riddles, ABC/numbers, etc.).
"""
import json
import logging
from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
]


def _call_gemini_resilient(client, prompt: str) -> str:
    for model_name in GEMINI_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Script model {model_name} note ({e}), trying next...")
    raise RuntimeError("All Gemini models temporarily unavailable")


def write_dual_scripts(config, topic1_data, topic2_data):
    """
    Generate two standalone, exciting scripts for Topic 1 and Topic 2.
    Each script is 30-38 words (~10-14s), perfectly tailored to its category.
    Returns: {"part1_script": str, "part2_script": str, "full_script": str}
    """
    client = genai.Client(api_key=config["gemini_api_key"])

    cat1 = topic1_data.get("category", "fun facts")
    top1 = topic1_data.get("topic", "Super Fun Story")
    hook1 = topic1_data.get("hook", "Look at this amazing adventure!")

    cat2 = topic2_data.get("category", "fairy tales")
    top2 = topic2_data.get("topic", "Magical Tale")
    hook2 = topic2_data.get("hook", "Once upon a time in a magic world!")

    prompt = f"""You are a top children's animator writing scripts for TWO SEPARATE YouTube Shorts for kids aged 3-8.

SHORT 1:
- Category: {cat1}
- Topic: {top1}
- Hook: {hook1}

SHORT 2:
- Category: {cat2} (DIFFERENT CATEGORY!)
- Topic: {top2}
- Hook: {hook2}

RULES FOR EACH SCRIPT:
- Must be a COMPLETE, standalone fun short story/fact/riddle (30-38 words, ~12 seconds of voiceover).
- Tailored specifically to its category:
  * If riddle: Ask the riddle question with excitement, pause 2 seconds, give the fun answer!
  * If fairy tale: Mini story with magical twist and happy moral!
  * If funny story: Silly situation with a hilarious punchline that makes kids giggle!
  * If science fact: Mind-blowing secret fact with simple kid-friendly explanation!
  * If ABC/numbers: Catchy rhyme or counting surprise!
- Super enthusiastic, high energy!
- Short sentences (max 8-10 words each).
- End with a friendly call to subscribe/follow!
- Absolutely NO emojis, NO special symbols.

Return ONLY raw valid JSON (no markdown fences, no triple backticks):
{{
  "part1_script": "Whoa! Benny the puppy blew a bubble so giant it lifted him into the sky! He floated past the birds and landed safely in a fluffy flower bush! That was hilarious! Subscribe for more funny stories!",
  "part2_script": "Once upon a time, a tiny mouse saw a giant dragon crying because of a splinter! The brave mouse pulled it out and they became best friends forever! Subscribe for more fairy tales!"
}}"""

    try:
        text = _call_gemini_resilient(client, prompt)

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        p1 = data.get("part1_script", "").strip()
        p2 = data.get("part2_script", "").strip()

        if not p1 or not p2:
            raise ValueError("Empty script returned")

        result = {
            "part1_script": p1,
            "part2_script": p2,
            "full_script": p1 + " " + p2
        }
        logger.info(f"Generated Script 1: {len(p1.split())} words | Script 2: {len(p2.split())} words")
        return result

    except Exception as e:
        logger.warning(f"Dual script generation failed ({e}), using fallback")
        p1 = f"{hook1} The world is full of hilarious surprises! Keep laughing and being curious my friend! Subscribe for more awesome fun daily!"
        p2 = f"{hook2} Always be kind and brave no matter how small you are! Subscribe for more magical adventures every single day!"
        return {
            "part1_script": p1,
            "part2_script": p2,
            "full_script": p1 + " " + p2
        }


# Backwards compatibility alias
def write_script(config, topic_data):
    if isinstance(topic_data, tuple) or isinstance(topic_data, list):
        return write_dual_scripts(config, topic_data[0], topic_data[1])
    # Fallback if called with single topic
    return write_dual_scripts(config, topic_data, topic_data)
