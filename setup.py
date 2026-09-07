#!/usr/bin/env python3
"""
setup.py — Run this ONCE to install everything.
After setup, you only need: python main.py
"""
import os
import sys
import subprocess
import json


def step(n, msg):
    print(f"\n[{n}] {msg}")


def pip_install(packages):
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + packages
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ⚠️  pip warning: {result.stderr[:300]}")
    return result.returncode == 0


def main():
    print("=" * 60)
    print("  YouTube Kids Shorts — First-time Setup")
    print("=" * 60)

    # 1. Install packages ─────────────────────────────────────────────────────
    step("1/5", "Installing Python packages (may take a minute)…")
    packages = [
        "google-generativeai>=0.8.0",
        "google-api-python-client>=2.0.0",
        "google-auth-oauthlib>=1.2.0",
        "google-auth-httplib2>=0.2.0",
        "moviepy>=1.0.3",
        "imageio-ffmpeg>=0.4.9",
        "Pillow>=10.0.0",
        "requests>=2.31.0",
        "edge-tts>=6.1.9",
        "numpy>=1.24.0",
    ]
    ok = pip_install(packages)
    print("   ✅  Packages installed!" if ok else "   ⚠️  Some packages had warnings — see above")

    # 2. Directories ──────────────────────────────────────────────────────────
    step("2/5", "Creating project directories…")
    for d in ["output", "logs", "pipeline"]:
        os.makedirs(d, exist_ok=True)
    print("   ✅  Directories: output/, logs/, pipeline/")

    # 3. config.json (only if missing) ────────────────────────────────────────
    step("3/5", "Creating config.json template…")
    if not os.path.exists("config.json"):
        cfg = {
            "_readme": "Fill in your 3 API keys. Never share this file publicly!",
            "gemini_api_key":               "YOUR_GEMINI_API_KEY_HERE",
            "pexels_api_key":               "YOUR_PEXELS_API_KEY_HERE",
            "channel_name":                 "Kids Fun Zone",
            "target_language":              "English",
            "video_duration_seconds":       20,
            "tts_voice":                    "en-US-AnaNeural",
            "youtube_client_secrets_path":  "client_secrets.json",
            "youtube_token_path":           "token.json",
            "video_category_id":            "27",
            "privacy_status":               "public",
            "output_dir":                   "output",
            "logs_dir":                     "logs",
            "history_db":                   "history.db",
        }
        with open("config.json", "w") as fh:
            json.dump(cfg, fh, indent=2)
        print("   ✅  config.json created — FILL IN YOUR API KEYS!")
    else:
        print("   ✅  config.json already exists")

    # 4. Pipeline __init__.py ─────────────────────────────────────────────────
    step("4/5", "Initialising pipeline package…")
    init_p = os.path.join("pipeline", "__init__.py")
    if not os.path.exists(init_p):
        with open(init_p, "w") as fh:
            fh.write("# YouTube Kids Shorts Pipeline\n")
    print("   ✅  pipeline/__init__.py ready")

    # 5. Quick dependency test ────────────────────────────────────────────────
    step("5/5", "Testing imports…")
    errors = []
    for pkg in ["google.generativeai", "moviepy.editor", "PIL", "edge_tts",
                "googleapiclient.discovery", "imageio_ffmpeg"]:
        try:
            __import__(pkg)
        except ImportError as e:
            errors.append(str(e))
    if errors:
        print(f"   ⚠️  Import issues: {errors}")
    else:
        print("   ✅  All imports OK!")

    print("\n" + "=" * 60)
    print("✅  Setup Complete!")
    print("=" * 60)
    print("""
Next steps (do these in order):

  STEP A — Add your API keys to config.json:
    • gemini_api_key  → aistudio.google.com  (you already have this)
    • pexels_api_key  → pexels.com/api       (free, takes 30 sec)

  STEP B — Set up YouTube access (ONE TIME):
    python setup_youtube_auth.py
    (Follow the link, sign in, done — token auto-saved)

  STEP C — Run daily:
    python main.py

  OPTIONAL — Auto-run every day at 9 AM:
    python schedule_daily.py
""")


if __name__ == "__main__":
    main()
