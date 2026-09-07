"""
script_writer.py - Uses Gemini AI (google-genai SDK) to write a 20-second
kids-friendly script split into 2 equal parts.
"""
import json
import logging
from google import genai

logger = logging.getLogger(__name__)


def write_script(config, topic_data):
    """Generate a 20-second script split into 2 x 10-second parts."""
    client = genai.Client(api_key=config["gemini_api_key"])

    duration    = config.get("video_duration_seconds", 20)
    total_words = int(duration * 2.5)   # ~2.5 words/sec kids TTS pace
    half_words  = total_words // 2

    prompt = f"""You are writing a YouTube Shorts narration script for kids (ages 3-10).

Topic: {topic_data["topic"]}
Hook (use this to start): {topic_data["hook"]}

RULES:
- Use VERY simple words that a 5-year-old understands
- Be excited, enthusiastic, and fun!
- Short punchy sentences (max 10 words each)
- No emojis, no symbols, no special characters in the script text
- Part 1 (~{half_words} words): Start with the hook, share 2 amazing facts
- Part 2 (~{half_words} words): Share 2 more facts, end with "Follow for more amazing facts!"
- Total = ~{total_words} words combined

Return ONLY raw valid JSON (no markdown, no triple backticks):
{{
    "part1_script": "Did you know giraffes have necks as long as a whole school bus! That is really really long! A giraffe uses its neck to reach leaves high up in the trees. Its tongue is also super long and dark purple!",
    "part2_script": "Baby giraffes are already taller than most adults when they are born! And giraffes only need to sleep about thirty minutes every day! They are amazing right? Follow for more amazing animal facts!"
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
        logger.info(f"Script ready. Words: {len(result['full_script'].split())}")
        return result

    except Exception as e:
        logger.warning(f"Script generation failed ({e}), using fallback")
        hook  = topic_data.get("hook", "This is absolutely amazing!")
        p1 = (
            f"{hook} "
            "Scientists have discovered so many incredible things about this! "
            "You will not believe how awesome nature really is. "
            "Every single day there are new surprises waiting to be found!"
        )
        p2 = (
            "There is so much more out there to learn and explore every day. "
            "The world is full of wonders that will blow your mind. "
            "Keep asking questions and keep being curious my friend. "
            "Follow for more amazing facts every single day!"
        )
        return {"part1_script": p1, "part2_script": p2, "full_script": p1 + " " + p2}
