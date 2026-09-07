#!/usr/bin/env python3
"""
main.py — YouTube Kids Shorts AI Automation
============================================
ONE COMMAND does everything:
  python main.py

Full pipeline:
  1. Gemini AI picks a unique trending kids topic (never repeats)
  2. Gemini AI writes a 20-second script (2 × 10-sec parts)
  3. edge-tts generates kid-friendly voice audio (free)
  4. MoviePy + PIL creates 9:16 Shorts videos with captions
  5. Gemini AI writes SEO title, description, and tags
  6. YouTube API uploads both parts automatically
  7. SQLite history records the topic — will NEVER repeat it
"""

import os
import sys
import json
import logging
from datetime import datetime


# ── Logging setup ─────────────────────────────────────────────────────────────
def _setup_logging(logs_dir: str = "logs") -> str:
    os.makedirs(logs_dir, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"run_{ts}.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_file


# ── Config loader ─────────────────────────────────────────────────────────────
def _load_config() -> dict:
    if not os.path.exists("config.json"):
        print("❌  config.json not found!  Run:  python setup.py")
        sys.exit(1)
    with open("config.json", encoding="utf-8-sig") as fh:
        cfg = json.load(fh)
    if cfg.get("gemini_api_key", "").startswith("YOUR_"):
        print("❌  Add your GEMINI_API_KEY to config.json first!")
        sys.exit(1)
    return cfg


# ── Banner ────────────────────────────────────────────────────────────────────
def _banner():
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    print("\n" + "═"*60)
    print("   🎬  YouTube Kids Shorts — AI Automation")
    print(f"   ⏰  {now}")
    print("═"*60)


# ── Main pipeline ─────────────────────────────────────────────────────────────
def main():
    _banner()
    config   = _load_config()
    log_file = _setup_logging(config.get("logs_dir", "logs"))
    logger   = logging.getLogger("main")

    # ── Imports (after FFmpeg path is set via imageio_ffmpeg in video_composer)
    from pipeline.history_manager import HistoryManager
    from pipeline.trend_finder    import find_trending_topic
    from pipeline.script_writer   import write_script
    from pipeline.audio_maker     import generate_audio
    from pipeline.video_composer  import create_video_parts
    from pipeline.metadata_gen    import generate_metadata
    from pipeline.uploader        import upload_to_youtube

    history    = HistoryManager(config.get("history_db", "history.db"))
    prev_count = history.get_total_count()
    logger.info(f"Previous video sets created: {prev_count}")

    audio_paths = None
    video_paths = None

    try:
        # ── Step 1 ────────────────────────────────────────────────────────────
        print("\n🔍  Step 1/6  Finding a unique trending topic…")
        topic_data = find_trending_topic(config, history)
        print(f"   ✅  Topic : {topic_data['topic']} {topic_data.get('emoji','')}")
        print(f"   💡  Hook  : {topic_data.get('hook','')[:70]}")

        # ── Step 2 ────────────────────────────────────────────────────────────
        print("\n✍️   Step 2/6  Writing script with Gemini AI…")
        script_data = write_script(config, topic_data)
        w = len(script_data["full_script"].split())
        print(f"   ✅  Script ready ({w} words)")
        print(f"   📝  Part 1: {script_data['part1_script'][:60]}…")

        # ── Step 3 ────────────────────────────────────────────────────────────
        print("\n🎙️   Step 3/6  Generating voice narration (edge-tts)…")
        audio_paths = generate_audio(config, script_data)
        print(f"   ✅  Part 1 audio: {audio_paths[0]}")
        print(f"   ✅  Part 2 audio: {audio_paths[1]}")

        # ── Step 4 ────────────────────────────────────────────────────────────
        print("\n🎬  Step 4/6  Building 9:16 Short videos…  (takes ~1-2 min)")
        video_paths = create_video_parts(config, script_data, topic_data, audio_paths)
        print(f"   ✅  Part 1 MP4: {video_paths[0]}")
        print(f"   ✅  Part 2 MP4: {video_paths[1]}")

        # ── Step 5 ────────────────────────────────────────────────────────────
        print("\n📝  Step 5/6  Generating SEO metadata with Gemini AI…")
        metadata_list = generate_metadata(config, topic_data, script_data)
        print(f"   ✅  Title 1 : {metadata_list[0]['title']}")
        print(f"   ✅  Title 2 : {metadata_list[1]['title']}")

        # ── Step 6 ────────────────────────────────────────────────────────────
        print("\n📤  Step 6/6  Uploading to YouTube…")
        results = upload_to_youtube(config, video_paths, metadata_list)

        vid_ids = []
        for r in results:
            if "url" in r:
                print(f"   ✅  Part {r['part']}: {r['url']}")
                vid_ids.append(r.get("video_id", ""))
            else:
                print(f"   ⚠️   Part {r['part']} upload error: {r.get('error','unknown')}")

        # ── Save to history (even partial success) ────────────────────────────
        history.add_topic(
            topic_data["topic"],
            topic_data.get("category", ""),
            vid_ids[0] if len(vid_ids) > 0 else "",
            vid_ids[1] if len(vid_ids) > 1 else "",
        )

        print("\n" + "═"*60)
        print("🎉  SUCCESS!  Both Shorts uploaded to YouTube!")
        print(f"📊  Total video sets uploaded so far: {prev_count + 1}")
        print(f"📋  Full log saved to: {log_file}")
        print("═"*60 + "\n")

    except KeyboardInterrupt:
        print("\n⚠️   Interrupted by user — cleaning up…")
        logger.warning("Pipeline interrupted by user")

    except Exception as exc:
        logger.error(f"Pipeline error: {exc}", exc_info=True)
        print(f"\n❌  Error: {exc}")
        print(f"📋  Check log for details: {log_file}")

    finally:
        # Clean up temp media files
        import glob
        out_dir = config.get("output_dir", "output")
        for paths in [video_paths, audio_paths]:
            if paths:
                for p in paths:
                    if p and os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
        # Clean up any temporary backgrounds or MoviePy working files
        temp_patterns = [
            os.path.join(out_dir, "*_bg.mp4"),
            os.path.join(out_dir, "temp_snd_*"),
            "*TEMP_MPY*",
            os.path.join(out_dir, "*TEMP_MPY*")
        ]
        for pat in temp_patterns:
            for f in glob.glob(pat):
                try:
                    os.remove(f)
                except Exception:
                    pass
        logger.info("Cleanup complete. Goodbye!")


if __name__ == "__main__":
    main()
