# 🎬 YouTube Kids Shorts — AI Automation

> One command. Two daily Shorts. Zero repetition. Forever.

## What It Does

Every time you run `python main.py`:

| Step | What happens |
|------|-------------|
| 1 | Gemini AI finds a trending kids topic (NEVER repeats one) |
| 2 | Gemini AI writes a fun 20-second script |
| 3 | edge-tts narrates it in a kid-friendly voice (free) |
| 4 | MoviePy builds 2 × 10-sec 9:16 Shorts videos with captions |
| 5 | Gemini AI writes SEO title, description & 10 tags |
| 6 | YouTube API uploads both parts automatically |
| 7 | Topic saved to history.db — never repeated ever |

---

## Quick Start (Do This Once)

### Step 1 — Install everything
```
python setup.py
```

### Step 2 — Add your 3 API keys to `config.json`

Open `config.json` and fill in:

| Key | Where to get it | Cost |
|-----|----------------|------|
| `gemini_api_key` | aistudio.google.com → Get API key | FREE (you have unlimited) |
| `pexels_api_key` | pexels.com/api → click "Get Started" (30 sec signup) | FREE |
| YouTube OAuth | See Step 3 below | FREE |

### Step 3 — Connect YouTube (one time only)
```
python setup_youtube_auth.py
```
A browser opens → sign in → done. Token auto-refreshes forever.

## Daily Usage

Every time you run:
```bash
python main.py
```

You will see an interactive menu to choose topics for today's **2 Shorts**:
```
   [1] 🏰 Fairy Tales
   [2] 🔬 Science Facts
   [3] 😂 Funny Stories
   [4] 🧩 Riddles
   [5] 🔤 ABC / Numbers
   [6] 🎲 Random (Let Gemini pick a fresh trending topic)
   [7] ✍️  Other / Custom (Type your own topic!)
```
- Choose any category for **Video 1** (or type your own custom topic with `7`!)
- Choose any category for **Video 2** (or type a second custom topic with `7`!)
- Or simply press **Enter** for full auto-pilot — Gemini picks two distinct categories!
- Both videos are completely independent Shorts (**NO "Part 1" or "Part 2" mentioned anywhere**).

---

## File Structure

```
YoutubeAutomation/
├── main.py                  ← THE ONLY COMMAND YOU NEED DAILY
├── setup.py                 ← Run once after fresh install
├── setup_youtube_auth.py    ← Run once to connect YouTube
├── schedule_daily.py        ← Optional: auto-run at set time
├── config.json              ← YOUR API KEYS (keep safe!)
├── requirements.txt
│
├── history.db               ← SQLite — topic history (never repeats)
│
├── pipeline/
│   ├── history_manager.py   ← Tracks all used topics
│   ├── trend_finder.py      ← Gemini: picks unique trending topic
│   ├── script_writer.py     ← Gemini: writes 20-sec kids script
│   ├── audio_maker.py       ← edge-tts: generates MP3 narration
│   ├── video_composer.py    ← PIL + MoviePy: builds 9:16 MP4
│   ├── metadata_gen.py      ← Gemini: title, description, tags
│   └── uploader.py          ← YouTube API: uploads both parts
│
├── output/                  ← Temp files (auto-deleted after upload)
└── logs/                    ← Run logs (one per day)
```

---

## What to Keep Safe

If you ever reinstall / get a new PC:

| File | Why |
|------|-----|
| `config.json` | Your API keys |
| `client_secrets.json` | YouTube OAuth app |
| `token.json` | YouTube login token |
| `history.db` | Topic history (prevents repeats) |

Just copy these 4 files to the new machine, run `python setup.py` once, done.

---

## Video Specs & Visual Features

| Setting | Value |
|---------|-------|
| Aspect Ratio | 9:16 (vertical Shorts) |
| Resolution | 1080 × 1920 px (Full HD) |
| FPS | 30 |
| Duration | ~10 sec each part |
| 3D Mascot | High-res Pixar/Disney style 3D cartoon character (1,500+ assets) with floating animation |
| Backgrounds | Gemini Veo AI Video -> Pexels HD Vertical Video -> Ken Burns Animated Photo |
| Subtitles | Shorts Safe-Zone (Y=1140-1360), high-contrast rounded pill box with stroke |
| Voiceover | Natural human conversational voice (`en-US-AvaNeural`) with +15% energetic pacing |
| Category | Education (Kids Safe, selfDeclaredMadeForKids = True) |

---

## Troubleshooting

**❌ "gemini_api_key starts with YOUR_"**
→ Open `config.json` and paste your real Gemini API key.

**❌ "client_secrets.json not found"**
→ Run `python setup_youtube_auth.py` and follow the instructions.

**❌ "All TTS voices failed"**
→ Check your internet connection. edge-tts needs internet.

**❌ Video is slow to render**
→ Normal — first render compiles frames. Subsequent runs are faster.

---

## Topic Categories

Gemini picks from 40+ categories including:
animals, space, dinosaurs, ocean creatures, science experiments,
geography, historical facts, fairy tales, riddles, jokes,
food facts, sports, nature, weather, numbers, ABC, superheroes,
robots, cooking, art, music, human body, transportation,
famous people, holidays, environment, and more!

