"""
audio_maker.py - Converts script text to MP3 using edge-tts (free, no API key).
Falls back through multiple kid-friendly voices if one fails.
"""
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Kid-friendly voices (ordered by preference)
KIDS_VOICES = [
    "en-US-AnaNeural",    # Young, cheerful female — best for kids
    "en-US-AriaNeural",   # Friendly female
    "en-US-JennyNeural",  # Warm, clear female
    "en-GB-MiaNeural",    # British female, clear
    "en-US-GuyNeural",    # Friendly male
]


async def _tts_async(text: str, voice: str, output_path: str):
    """Async helper: generate TTS and save to file."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def _generate_one(text: str, voice: str, output_path: str):
    """Generate a single audio file, trying voices in order if one fails."""
    voices_to_try = [voice] + [v for v in KIDS_VOICES if v != voice]

    for v in voices_to_try:
        try:
            logger.info(f"TTS: voice={v}, output={output_path}")
            asyncio.run(_tts_async(text, v, output_path))
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Audio saved ({os.path.getsize(output_path)//1024} KB)")
                return output_path
        except Exception as e:
            logger.warning(f"Voice {v} failed: {e}")

    raise RuntimeError("All TTS voices failed — check internet connection.")


def generate_audio(config: dict, script_data: dict):
    """
    Generate audio for Part 1 and Part 2 of the script.

    Returns:
        (part1_audio_path, part2_audio_path)
    """
    voice = config.get("tts_voice", "en-US-AnaNeural")
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    part1_path = os.path.join(output_dir, "part1_audio.mp3")
    part2_path = os.path.join(output_dir, "part2_audio.mp3")

    logger.info("Generating Part 1 audio...")
    _generate_one(script_data["part1_script"], voice, part1_path)

    logger.info("Generating Part 2 audio...")
    _generate_one(script_data["part2_script"], voice, part2_path)

    return part1_path, part2_path


def get_audio_duration(audio_path: str) -> float:
    """Return duration of an audio file in seconds."""
    try:
        from moviepy.editor import AudioFileClip
        clip = AudioFileClip(audio_path)
        dur = clip.duration
        clip.close()
        return dur
    except Exception as e:
        logger.warning(f"Could not read audio duration ({e}), defaulting to 10s")
        return 10.0
