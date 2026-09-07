"""
metadata_gen.py - Generates SEO-optimised YouTube title, description, and tags
for both video parts using Gemini AI (google-genai SDK).
"""
import json
import logging
from google import genai

logger = logging.getLogger(__name__)


def generate_metadata(config, topic_data, script_data):
    """
    Generate YouTube metadata for Part 1 and Part 2.
    Returns: [part1_meta_dict, part2_meta_dict]
    """
    client  = genai.Client(api_key=config["gemini_api_key"])
    channel = config.get("channel_name", "Kids Fun Zone")
    topic   = topic_data["topic"]

    prompt = f"""You are a YouTube SEO expert specialising in kids educational Shorts.

Topic  : {topic}
Channel: {channel}
Part 1 script (first 200 chars): {script_data["part1_script"][:200]}
Part 2 script (first 200 chars): {script_data["part2_script"][:200]}

Create YouTube Shorts metadata for BOTH parts.

Rules:
- Titles: max 70 chars, catchy, include "Part 1" and "Part 2", include #Shorts
- Descriptions: 150-280 chars, keyword-rich, end with "Follow for more!" include #Shorts #Kids
- Tags: exactly 10 tags, mix of broad ("kids shorts") and specific ("cat facts for kids")
- Use emojis in titles and descriptions to boost click-through

Return ONLY raw valid JSON (no markdown, no triple backticks):
{{
    "part1": {{
        "title": "Why Giraffes Have Long Necks! Part 1 #Shorts",
        "description": "Did you know a giraffe neck is as long as a school bus? Mind-blowing animal facts for curious kids! Like and Follow for more daily fun facts! #Shorts #Kids #Animals #FunFacts",
        "tags": ["giraffe facts", "animals for kids", "kids shorts", "fun facts for kids", "educational shorts", "amazing animals", "kids learning", "animal facts", "shorts for kids", "giraffe"]
    }},
    "part2": {{
        "title": "Why Giraffes Have Long Necks! Part 2 #Shorts",
        "description": "Baby giraffes are taller than adults the day they are born! More incredible giraffe facts for kids! Follow for daily amazing facts! #Shorts #Kids #Animals #FunFacts",
        "tags": ["giraffe facts", "animals for kids", "kids shorts", "fun facts for kids", "educational shorts", "amazing animals", "kids learning", "animal facts", "shorts for kids", "giraffe"]
    }}
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
        meta = [data["part1"], data["part2"]]

        for m in meta:
            if "#Shorts" not in m["title"] and "#shorts" not in m["title"]:
                m["title"] = m["title"][:65] + " #Shorts"
            m["title"]       = m["title"][:100]
            m["description"] = m["description"][:5000]
            m["tags"]        = m["tags"][:15]

        logger.info(f"Metadata ready: {meta[0]['title']}")
        return meta

    except Exception as e:
        logger.warning(f"Metadata generation failed ({e}), using fallback")
        base = topic[:50]
        common_tags = ["kids shorts", "fun facts for kids", "educational", "children",
                       "learning", "amazing facts", "kids content", "shorts", "kids",
                       topic.lower().split()[0] if topic else "facts"]
        return [
            {
                "title":       f"{base} - Fun Facts! Part 1 #Shorts",
                "description": (f"Amazing facts about {topic} for kids! Part 1 of 2. "
                                f"Educational and fun! Follow for more daily facts! "
                                f"#Shorts #Kids #Educational #FunFacts"),
                "tags": common_tags,
            },
            {
                "title":       f"{base} - Fun Facts! Part 2 #Shorts",
                "description": (f"More amazing facts about {topic} for kids! Part 2 of 2. "
                                f"Follow for daily fun educational shorts! "
                                f"#Shorts #Kids #Educational #FunFacts"),
                "tags": common_tags,
            },
        ]
