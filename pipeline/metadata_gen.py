"""
metadata_gen.py - Generates SEO-optimised YouTube titles, descriptions, and tags
for Part 1 and Part 2, each tailored to its specific topic and category.
"""
import json
import logging
from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
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
            logger.warning(f"Metadata model {model_name} note ({e}), trying next...")
    raise RuntimeError("All Gemini models temporarily unavailable")


def generate_metadata_for_two_topics(config, topic1_data, topic2_data, script_data):
    """
    Generate YouTube Shorts metadata for Part 1 and Part 2 with distinct topics.
    Returns: [part1_meta, part2_meta]
    """
    client = genai.Client(api_key=config["gemini_api_key"])
    channel = config.get("channel_name", "Kids Fun Zone")

    t1_title = topic1_data.get("topic", "Fun Kids Short 1")
    t1_cat = topic1_data.get("category", "kids")
    p1_script = script_data.get("part1_script", "")

    t2_title = topic2_data.get("topic", "Fun Kids Short 2")
    t2_cat = topic2_data.get("category", "kids")
    p2_script = script_data.get("part2_script", "")

    prompt = f"""You are a YouTube SEO expert specialising in kids educational and entertainment Shorts.

Channel: {channel}

VIDEO 1:
- Category: {t1_cat}
- Topic: {t1_title}
- Script: {p1_script}

VIDEO 2:
- Category: {t2_cat}
- Topic: {t2_title}
- Script: {p2_script}

Create catchy YouTube Shorts metadata for BOTH videos.

RULES:
- ABSOLUTELY DO NOT write "Part 1", "Part 2", or "Part 1 of 2" anywhere in the titles or descriptions!
- Each video is an independent standalone Short.
- Titles: max 65 chars, catchy, start with topic, include category emoji, include #Shorts.
- Descriptions: 150-250 chars, engaging, include #Shorts #Kids #{t1_cat.replace(' ', '')} and end with "Subscribe for more!".
- Tags: 8-12 high-traffic tags for each.

Return ONLY raw valid JSON (no markdown fences, no triple backticks):
{{
  "part1": {{
    "title": "{t1_title[:50]}! 🌟 #Shorts",
    "description": "Watch this super exciting {t1_cat} short for kids! Learn, laugh, and explore! Subscribe for more daily kids fun! #Shorts #Kids #FunFacts",
    "tags": ["kids shorts", "shorts for kids", "{t1_cat}", "fun for kids", "educational shorts"]
  }},
  "part2": {{
    "title": "{t2_title[:50]}! ✨ #Shorts",
    "description": "Another amazing {t2_cat} adventure! Like and follow for magical daily shorts! #Shorts #Kids #FunFacts",
    "tags": ["kids shorts", "shorts for kids", "{t2_cat}", "fun for kids", "educational shorts"]
  }}
}}"""

    try:
        text = _call_gemini_resilient(client, prompt)

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)
        meta = [data["part1"], data["part2"]]

        for m in meta:
            # Strip any accidental Part 1 / Part 2 strings
            for bad in ["Part 1", "Part 2", "part 1", "part 2", "PART 1", "PART 2", "Part 1 of 2", "Part 2 of 2"]:
                m["title"] = m["title"].replace(f"- {bad}", "").replace(f"• {bad}", "").replace(bad, "").strip()
                m["description"] = m["description"].replace(bad, "").strip()

            if "#Shorts" not in m["title"] and "#shorts" not in m["title"]:
                m["title"] = m["title"][:60] + " #Shorts"
            m["title"] = m["title"][:100]
            m["description"] = m["description"][:5000]
            m["tags"] = m["tags"][:15]

        logger.info(f"Metadata ready: '{meta[0]['title']}' & '{meta[1]['title']}'")
        return meta

    except Exception as e:
        logger.warning(f"Metadata generation failed ({e}), using fallback")
        return [
            {
                "title": f"{t1_title[:50]}! #Shorts",
                "description": f"Exciting {t1_cat} for kids! Subscribe for daily fun shorts! #Shorts #Kids #{t1_cat.replace(' ', '')}",
                "tags": ["kids shorts", "shorts for kids", t1_cat, "fun facts for kids", "kids learning"]
            },
            {
                "title": f"{t2_title[:50]}! #Shorts",
                "description": f"Amazing {t2_cat} adventure for kids! Subscribe for more daily videos! #Shorts #Kids #{t2_cat.replace(' ', '')}",
                "tags": ["kids shorts", "shorts for kids", t2_cat, "fun facts for kids", "kids learning"]
            }
        ]


# Backwards compatibility alias
def generate_metadata(config, topic_data, script_data):
    if isinstance(topic_data, tuple) or isinstance(topic_data, list):
        return generate_metadata_for_two_topics(config, topic_data[0], topic_data[1], script_data)
    return generate_metadata_for_two_topics(config, topic_data, topic_data, script_data)
