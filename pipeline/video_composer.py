"""
video_composer.py
=================
Creates 9:16 YouTube Shorts videos (1080x1920) using PIL + MoviePy v2.
- Downloads background image from Pexels (or uses a colourful gradient fallback)
- Renders animated captions sentence by sentence as audio plays
- Splits into Part 1 and Part 2 MP4 files
- NO ImageMagick needed — pure PIL + numpy
- Compatible with MoviePy 2.x
"""
import os
import re
import logging
import requests
import numpy as np
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

W, H = 1080, 1920   # 9:16 Shorts
FPS  = 30

DEFAULT_PALETTES = [
    ("#FF6B6B", "#FFE66D"),
    ("#667EEA", "#764BA2"),
    ("#11998E", "#38EF7D"),
    ("#F7971E", "#FFD200"),
    ("#1A78C2", "#4ECDC4"),
    ("#C94B4B", "#4B134F"),
    ("#43C6AC", "#191654"),
    ("#FF8008", "#FFC837"),
]

# ── Font helpers ──────────────────────────────────────────────────────────────
def _get_font(style: str, size: int):
    paths = {
        "bold":   [r"C:\Windows\Fonts\arialbd.ttf",  r"C:\Windows\Fonts\calibrib.ttf"],
        "regular":[r"C:\Windows\Fonts\arial.ttf",    r"C:\Windows\Fonts\calibri.ttf"],
        "comic":  [r"C:\Windows\Fonts\comicbd.ttf",  r"C:\Windows\Fonts\comic.ttf"],
        "emoji":  [r"C:\Windows\Fonts\seguiemj.ttf", r"C:\Windows\Fonts\segoeui.ttf"],
    }
    for path in paths.get(style, paths["regular"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

# ── Background helpers ────────────────────────────────────────────────────────
def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _gradient_bg(colors) -> Image.Image:
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    c1 = _hex_to_rgb(colors[0]) if isinstance(colors[0], str) else tuple(colors[0])
    c2 = _hex_to_rgb(colors[1]) if isinstance(colors[1], str) else tuple(colors[1])
    for y in range(H):
        t = y / H
        r = int(c1[0]*(1-t) + c2[0]*t)
        g = int(c1[1]*(1-t) + c2[1]*t)
        b = int(c1[2]*(1-t) + c2[2]*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    return img

def _pexels_bg(api_key: str, query: str):
    if not api_key or api_key.startswith("YOUR_"):
        return None
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": f"{query} colorful bright", "per_page": 5,
                    "orientation": "portrait", "size": "large"},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        photos = resp.json().get("photos", [])
        if not photos:
            return None
        url = photos[0]["src"]["large2x"]
        img = Image.open(BytesIO(requests.get(url, timeout=30).content)).convert("RGB")
        # Centre-crop to 9:16
        tr = W / H
        if (img.width / img.height) > tr:
            nw = int(img.height * tr)
            left = (img.width - nw) // 2
            img = img.crop((left, 0, left+nw, img.height))
        else:
            nh = int(img.width / tr)
            top = (img.height - nh) // 2
            img = img.crop((0, top, img.width, top+nh))
        img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(radius=2))
        return img
    except Exception as e:
        logger.warning(f"Pexels fetch failed: {e}")
        return None

# ── Drawing helpers ───────────────────────────────────────────────────────────
def _shadow(draw, xy, text, font, fill=(255,255,255), shadow=(0,0,0), offset=4):
    x, y = xy
    draw.text((x+offset, y+offset), text, font=font, fill=shadow)
    draw.text((x, y),               text, font=font, fill=fill)

def _wrap(text: str, font, max_w: int, draw) -> list:
    words, lines, cur = text.split(), [], []
    for w in words:
        test = " ".join(cur+[w])
        bb   = draw.textbbox((0,0), test, font=font)
        if bb[2]-bb[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

# ── Frame renderer ────────────────────────────────────────────────────────────
def _render_frame(bg, title, phrase, part_num, emoji_text, progress) -> np.ndarray:
    frame = bg.copy().convert("RGBA")
    ov    = Image.new("RGBA", (W, H), (0,0,0,0))
    od    = ImageDraw.Draw(ov)
    for y in range(350):
        a = int(160*(1-y/350))
        od.line([(0,y),(W,y)], fill=(0,0,0,a))
    for y in range(H-600, H):
        a = int(210*(y-(H-600))/600)
        od.line([(0,y),(W,y)], fill=(0,0,0,a))
    frame = Image.alpha_composite(frame, ov).convert("RGB")
    draw  = ImageDraw.Draw(frame)

    # PART badge
    bf    = _get_font("bold", 38)
    badge = f"PART {part_num} of 2"
    bb    = draw.textbbox((0,0), badge, font=bf)
    bw, bh = bb[2]-bb[0]+44, bb[3]-bb[1]+22
    draw.rounded_rectangle([28, 48, 28+bw, 48+bh], radius=16, fill=(255,200,0))
    draw.text((28+22, 48+11), badge, font=bf, fill=(0,0,0))

    # KIDS ZONE badge
    kf  = _get_font("bold", 34)
    ktxt= "KIDS ZONE"
    kb  = draw.textbbox((0,0), ktxt, font=kf)
    kw  = kb[2]-kb[0]+44
    draw.rounded_rectangle([W-kw-28, 48, W-28, 48+bh], radius=16, fill=(255,80,80))
    draw.text((W-kw-6, 48+11), ktxt, font=kf, fill=(255,255,255))

    # Title
    tf     = _get_font("bold", 60)
    tlines = _wrap(title, tf, W-80, draw)
    ty     = 140
    for line in tlines[:3]:
        tb = draw.textbbox((0,0), line, font=tf)
        x  = (W-(tb[2]-tb[0]))//2
        _shadow(draw, (x,ty), line, tf)
        ty += tb[3]-tb[1]+8

    # Emoji label in centre (use text approximation since emoji fonts vary)
    lf  = _get_font("bold", 160)
    try:
        lb  = draw.textbbox((0,0), emoji_text, font=lf)
        draw.text(((W-(lb[2]-lb[0]))//2, H//2-200), emoji_text, font=lf, fill=(255,255,255,200))
    except Exception:
        pass

    # Caption
    cf     = _get_font("comic", 58)
    clines = _wrap(phrase, cf, W-80, draw)
    lhs    = []
    for ln in clines:
        cb = draw.textbbox((0,0), ln, font=cf)
        lhs.append(cb[3]-cb[1]+18)
    total_h = sum(lhs)
    cy = H - total_h - 130
    for i, line in enumerate(clines):
        cb = draw.textbbox((0,0), line, font=cf)
        x  = (W-(cb[2]-cb[0]))//2
        _shadow(draw, (x,cy), line, cf, fill=(255,255,120), offset=4)
        cy += lhs[i]

    # Progress bar
    draw.rectangle([0, H-14, W, H], fill=(200,200,200))
    if progress > 0:
        draw.rectangle([0, H-14, int(W*progress), H], fill=(255,200,0))

    return np.array(frame)

# ── Video part builder ────────────────────────────────────────────────────────
def _build_part(bg, title, script, part_num, emoji_text, audio_path, output_path):
    import imageio_ffmpeg
    from moviepy import AudioFileClip, VideoClip
    import moviepy.config as mconf
    mconf.FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

    audio    = AudioFileClip(audio_path)
    duration = audio.duration

    sents = re.split(r"(?<=[.!?])\s+", script.strip())
    sents = [s.strip() for s in sents if s.strip()] or [script]
    spf   = duration / len(sents)

    def make_frame(t):
        idx      = min(int(t/spf), len(sents)-1)
        progress = t/duration
        return _render_frame(bg, title, sents[idx], part_num, emoji_text, progress)

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_audio(audio).with_fps(FPS)

    logger.info(f"Rendering Part {part_num} -> {output_path}")
    clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=FPS,
        preset="ultrafast",
        logger=None,
    )
    audio.close()
    clip.close()
    logger.info(f"Part {part_num} done.")
    return output_path

# ── Public entry point ────────────────────────────────────────────────────────
def create_video_parts(config, script_data, topic_data, audio_paths):
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    title      = topic_data.get("topic",        "Fun Facts for Kids")
    emoji_text = topic_data.get("emoji",         "STAR")
    colors     = topic_data.get("color_scheme",  DEFAULT_PALETTES[0])

    logger.info("Fetching background image...")
    bg = _pexels_bg(config.get("pexels_api_key",""), topic_data.get("category","colorful"))
    if bg is None:
        logger.info("Using gradient background")
        bg = _gradient_bg(colors)

    p1 = os.path.join(output_dir, "part1.mp4")
    p2 = os.path.join(output_dir, "part2.mp4")

    _build_part(bg, title, script_data["part1_script"], 1, emoji_text, audio_paths[0], p1)
    _build_part(bg, title, script_data["part2_script"], 2, emoji_text, audio_paths[1], p2)

    return [p1, p2]
