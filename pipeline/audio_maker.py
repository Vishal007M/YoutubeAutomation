"""
audio_maker.py - Converts script text to MP3 using edge-tts.
Uses modern, expressive human-like voices with natural conversational pacing (+15% speech rate).
"""
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Natural, human-like, expressive conversational voices (ordered by quality & engagement)
HUMAN_VOICES = [
    "en-US-AvaNeural",         # Most natural, expressive modern American female
    "en-US-EmmaNeural",        # Warm, cheerful, conversational storytelling female
    "en-US-AndrewNeural",      # Natural, energetic storytelling male
    "en-US-AriaNeural",        # Dynamic, broadcast-quality female
    "en-US-ChristopherNeural", # Friendly, warm conversational male
]


async def _tts_async(text: str, voice: str, rate: str, output_path: str):
    """Async helper: generate TTS with natural human pacing and save to file."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def _generate_one(text: str, voice: str, rate: str, output_path: str):
    """Generate a single audio file, trying voices in order if one fails."""
    voices_to_try = [voice] + [v for v in HUMAN_VOICES if v != voice]

    for v in voices_to_try:
        try:
            logger.info(f"TTS: voice={v}, rate={rate}, output={output_path}")
            asyncio.run(_tts_async(text, v, rate, output_path))
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Audio saved successfully ({os.path.getsize(output_path)//1024} KB)")
                return output_path
        except Exception as e:
            logger.warning(f"Voice {v} failed: {e}")

    raise RuntimeError("All TTS voices failed - check internet connection.")


def generate_audio(config: dict, script_data: dict):
    """
    Generate audio for Part 1 and Part 2 with natural human pacing.

    Returns:
        (part1_audio_path, part2_audio_path)
    """
    voice = config.get("tts_voice", "en-US-AvaNeural")
    rate = config.get("tts_rate", "+15%")  # Natural lively human pacing (not sluggish)
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    part1_path = os.path.join(output_dir, "part1_audio.mp3")
    part2_path = os.path.join(output_dir, "part2_audio.mp3")

    logger.info("Generating Part 1 audio (human-like pacing)...")
    _generate_one(script_data["part1_script"], voice, rate, part1_path)

    logger.info("Generating Part 2 audio (human-like pacing)...")
    _generate_one(script_data["part2_script"], voice, rate, part2_path)

    return part1_path, part2_path


def get_audio_duration(audio_path: str) -> float:
    """Return duration of an audio file in seconds."""
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(audio_path)
        dur = clip.duration
        clip.close()
        return dur
    except Exception as e:
        logger.warning(f"Could not read audio duration ({e}), defaulting to 10s")
        return 10.0
