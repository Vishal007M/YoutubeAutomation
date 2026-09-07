"""
veo_generator.py - Optional Gemini Veo AI video generation integration.
Tries to generate custom video using Google Veo models if available/funded,
with graceful fallback if quota or feature is unavailable.
"""
import os
import time
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def try_generate_veo_video(config: dict, prompt: str, output_path: str) -> str | None:
    """
    Attempt to generate video using Gemini Veo.
    Returns the saved MP4 file path on success, or None on quota/error.
    """
    api_key = config.get("gemini_api_key", "")
    if not api_key or api_key.startswith("YOUR_"):
        return None

    try:
        logger.info(f"Checking Gemini Veo video generation for prompt: {prompt[:60]}...")
        client = genai.Client(api_key=api_key)

        # Try fast preview model first
        op = client.models.generate_videos(
            model="veo-3.1-lite-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds=5
            )
        )

        logger.info(f"Veo operation started: {op.name}. Waiting for completion...")
        # Poll operation if started
        while not op.done:
            time.sleep(8)
            op = client.operations.get(op)

        if op.response and op.response.generated_videos:
            vid = op.response.generated_videos[0]
            with open(output_path, "wb") as f:
                f.write(vid.video.video_bytes)
            logger.info(f"Veo video successfully generated: {output_path}")
            return output_path

    except Exception as e:
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            logger.info("Gemini Veo quota not active on this tier. Proceeding with Pexels HD video.")
        else:
            logger.info(f"Gemini Veo note ({err_msg[:100]}). Proceeding with Pexels HD video.")

    return None
