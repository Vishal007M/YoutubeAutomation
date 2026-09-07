"""
script_writer.py - Generates highly engaging, fun, kid-friendly scripts for Shorts.
Uses dynamic storytelling, excitement, and clear pacing for young kids.
"""
import json
import logging
from google import genai

logger = logging.getLogger(__name__)


def write_script(config, topic_data):
    """Generate an enthusiastic kids script split into Part 1 and Part 2."""
    client = genai.Client(api_key=config["gemini_api_key"])

    duration    = config.get("video_duration_seconds", 20)
    total_words = int(duration * 2.5)   # ~2.5 words/sec pace
    half_words  = total_words // 2

    prompt = f"""You are a professional children's TV host (like Blippi or Bluey) writing an ultra-fun YouTube Shorts script for kids aged 3-8.

Topic: {topic_data["topic"]}
Subject: {topic_data.get("subject", "nature")}
Hook: {topic_data["hook"]}

STYLE REQUIREMENTS:
- Super enthusiastic, high energy, and friendly!
- Start with an exciting exclamation ("Whoa!", "Guess what?", "Look!")
- Use very simple words a 4-year-old understands easily
- Punchy, short sentences (max 8-10 words each)
- Absolutely NO emojis or special symbols in the text
- Part 1 (~{half_words} words): Deliver the hook and 2 crazy fun facts that blow kids' minds!
- Part 2 (~{half_words} words): Give 2 more unbelievable facts, then end with "Subscribe for more awesome fun facts!"

Return ONLY raw valid JSON (no markdown fences, no triple backticks):
{{
    "part1_script": "Whoa! Look at this! Did you know giraffes have necks as long as a whole school bus? That is huge! Their tongues are super long and dark purple to eat prickly acacia leaves! Wow!",
    "part2_script": "Guess what else! Baby giraffes can stand up and run just thirty minutes after being born! And adult giraffes only sleep thirty minutes a day! Subscribe for more awesome fun facts!"
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

        data = json.loads(text)
        p1   = data.get("part1_script", "").strip()
        p2   = data.get("part2_script", "").strip()

        if not p1 or not p2:
            raise ValueError("Empty script parts returned")

        result = {"part1_script": p1, "part2_script": p2, "full_script": p1 + " " + p2}
        logger.info(f"Script generated ({len(result['full_script'].split())} words)")
        return result

    except Exception as e:
        logger.warning(f"Script generation failed ({e}), using fallback")
        hook = topic_data.get("hook", "Whoa! This is super amazing!")
        p1 = (
            f"Whoa! {hook} "
            "Nature has so many crazy surprises waiting for you! "
            "Scientists discovered this and everyone was completely shocked! "
            "Are you ready to learn the secret?"
        )
        p2 = (
            "Here is another crazy fact! "
            "This happens every single day right here on our planet! "
            "Learning new things is the best superpower ever! "
            "Subscribe for more awesome fun facts every single day!"
        )
        return {"part1_script": p1, "part2_script": p2, "full_script": p1 + " " + p2}
