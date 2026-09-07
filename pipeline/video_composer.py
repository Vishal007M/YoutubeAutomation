"""
video_composer.py
=================
Next-Gen 9:16 Kids YouTube Shorts Video Engine (1080x1920)
- Video Background: Gemini Veo AI video -> Pexels HD Vertical Video -> Ken Burns Animated Photo
- Mascot: High-res 3D Pixar/Disney style cartoon character with gentle floating animation
- Safe-Zone Subtitles: Placed at Y=1080-1360, completely clear of YouTube bottom UI (Y=1470+)
- High-contrast rounded pill box captions with stroke for maximum legibility
- Zero broken glyph boxes!
"""
import os
import re
import math
import logging
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from pipeline.character_manager import get_3d_character_image
from pipeline.veo_generator import try_generate_veo_video

logger = logging.getLogger(__name__)

W, H = 1080, 1920   # 9:16 Shorts standard
FPS  = 30

DEFAULT_PALETTES = [
    ("#FF5E62", "#FF9966"),  # Sunrise coral
    ("#4E54C8", "#8F94FB"),  # Deep blue-violet
    ("#11998E", "#38EF7D"),  # Emerald mint
    ("#F7971E", "#FFD200"),  # Sunny gold
    ("#00C9FF", "#92FE9D"),  # Tropical lagoon
    ("#FC466B", "#3F5EFB"),  # Bubblegum berry
]


def _get_font(style: str, size: int) -> ImageFont.FreeTypeFont:
    """Load Windows font safely with fallback."""
    paths = {
        "bold":    [r"C:\Windows\Fonts\arialbd.ttf",  r"C:\Windows\Fonts\calibrib.ttf", r"C:\Windows\Fonts\segoeuib.ttf"],
        "heavy":   [r"C:\Windows\Fonts\impact.ttf",   r"C:\Windows\Fonts\arialbd.ttf"],
        "comic":   [r"C:\Windows\Fonts\comicbd.ttf",  r"C:\Windows\Fonts\comic.ttf",   r"C:\Windows\Fonts\arialbd.ttf"],
        "regular": [r"C:\Windows\Fonts\arial.ttf",    r"C:\Windows\Fonts\calibri.ttf"],
    }
    for path in paths.get(style, paths["bold"]):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _make_gradient_frame(colors, t: float) -> Image.Image:
    """Animated smooth vertical gradient."""
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    c1 = _hex_to_rgb(colors[0])
    c2 = _hex_to_rgb(colors[1])
    # subtle wave shift
    shift = int(30 * math.sin(2 * math.pi * t * 0.2))
    for y in range(H):
        ratio = max(0.0, min(1.0, (y + shift) / H))
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _download_pexels_video(api_key: str, query: str, output_path: str) -> str | None:
    """Search and download a portrait HD video clip from Pexels."""
    if not api_key or api_key.startswith("YOUR_"):
        return None
    try:
        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": 5, "orientation": "portrait"}
        resp = requests.get(url, headers=headers, params=params, timeout=12)
        if resp.status_code != 200:
            return None

        videos = resp.json().get("videos", [])
        if not videos:
            # Fallback to broader query
            params["query"] = query.split()[0]
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            videos = resp.json().get("videos", [])

        if not videos:
            return None

        # Find best 1080p or 720p portrait video file
        best_file = None
        for v in videos:
            files = v.get("video_files", [])
            for f in files:
                w = f.get("width", 0)
                h = f.get("height", 0)
                if f.get("file_type") == "video/mp4" and h > w:
                    if w in (1080, 720):
                        best_file = f.get("link")
                        break
                    elif not best_file:
                        best_file = f.get("link")
            if best_file:
                break

        if best_file:
            logger.info(f"Downloading Pexels HD video: {best_file[:65]}...")
            vid_resp = requests.get(best_file, timeout=45)
            with open(output_path, "wb") as fh:
                fh.write(vid_resp.content)
            return output_path

    except Exception as e:
        logger.warning(f"Pexels video download note: {e}")
    return None


def _download_pexels_image(api_key: str, query: str) -> Image.Image | None:
    """Download a high quality Pexels portrait photo."""
    if not api_key or api_key.startswith("YOUR_"):
        return None
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": query, "per_page": 4, "orientation": "portrait"}
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        photos = resp.json().get("photos", [])
        if photos:
            img_url = photos[0]["src"].get("large2x") or photos[0]["src"].get("large")
            img_resp = requests.get(img_url, timeout=20)
            img = Image.open(requests.compat.BytesIO(img_resp.content)).convert("RGB")
            # Center crop to 9:16
            tr = W / H
            if (img.width / img.height) > tr:
                nw = int(img.height * tr)
                left = (img.width - nw) // 2
                img = img.crop((left, 0, left + nw, img.height))
            else:
                nh = int(img.width / tr)
                top = (img.height - nh) // 2
                img = img.crop((0, top, img.width, top + nh))
            return img.resize((W, H), Image.LANCZOS)
    except Exception as e:
        logger.warning(f"Pexels image note: {e}")
    return None


def _wrap_text(text: str, font, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        bb = draw.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _draw_text_with_outline(draw: ImageDraw.ImageDraw, xy, text: str, font,
                            fill_color, outline_color=(0, 0, 0), outline_width=5):
    """Render text with a heavy crisp cartoon outline."""
    x, y = xy
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill_color)


def _render_short_frame(
    bg_frame: Image.Image,
    character_img: Image.Image,
    title: str,
    caption: str,
    badge_text: str,
    t: float,
    duration: float
) -> np.ndarray:
    """
    Renders a single frame with:
    - Background (video frame or animated photo)
    - Animated floating 3D character mascot
    - Safe-Zone pill caption (Y=1100 to 1360)
    - Part & Kids Zone badges
    - Progress bar
    """
    frame = bg_frame.copy().convert("RGBA")

    # Dark gradient overlays at top (for title) and very bottom (for YouTube UI)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    # Top vignette for badges & title
    for y in range(320):
        alpha = int(170 * (1.0 - y / 320))
        odraw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
    # Bottom vignette for YouTube Shorts UI safe zone
    for y in range(H - 460, H):
        alpha = int(190 * ((y - (H - 460)) / 460))
        odraw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

    frame = Image.alpha_composite(frame, overlay)

    # 1. Floating 3D Character Mascot (Center: Y=450-950)
    if character_img:
        # Sine bobbing motion: +/- 18 pixels
        bob_offset = int(18 * math.sin(2 * math.pi * t * 0.75))
        cw, ch = character_img.size
        cx = (W - cw) // 2
        cy = 470 + bob_offset
        frame.paste(character_img, (cx, cy), character_img)

    draw = ImageDraw.Draw(frame)

    # 2. Top Badges
    badge_font = _get_font("bold", 34)
    bb = draw.textbbox((0, 0), badge_text, font=badge_font)
    bw, bh = (bb[2] - bb[0]) + 36, (bb[3] - bb[1]) + 20
    draw.rounded_rectangle([35, 50, 35 + bw, 50 + bh], radius=16, fill=(255, 195, 0))
    draw.text((35 + 18, 50 + 10), badge_text, font=badge_font, fill=(15, 15, 15))

    kz_font = _get_font("bold", 34)
    kz_text = "KIDS ZONE"
    kb = draw.textbbox((0, 0), kz_text, font=kz_font)
    kw = (kb[2] - kb[0]) + 40
    draw.rounded_rectangle([W - kw - 35, 50, W - 35, 50 + bh], radius=16, fill=(255, 75, 75))
    draw.text((W - kw - 15, 50 + 11), kz_text, font=kz_font, fill=(255, 255, 255))

    # 3. Main Title (Top: Y=145 to 310)
    title_font = _get_font("heavy", 56)
    t_lines = _wrap_text(title, title_font, W - 100, draw)[:3]
    cur_ty = 148
    for line in t_lines:
        tbb = draw.textbbox((0, 0), line, font=title_font)
        tx = (W - (tbb[2] - tbb[0])) // 2
        _draw_text_with_outline(draw, (tx, cur_ty), line, title_font, (255, 255, 255), (0, 0, 0), 6)
        cur_ty += (tbb[3] - tbb[1]) + 10

    # 4. Safe-Zone Subtitles (Y=1100 to 1360, SAFE FROM YOUTUBE CONTROLS!)
    if caption:
        cap_font = _get_font("comic", 54)
        c_lines = _wrap_text(caption, cap_font, W - 140, draw)

        # Calculate pill box bounding box
        line_heights = []
        max_line_w = 0
        for cl in c_lines:
            cbb = draw.textbbox((0, 0), cl, font=cap_font)
            lw = cbb[2] - cbb[0]
            lh = cbb[3] - cbb[1]
            max_line_w = max(max_line_w, lw)
            line_heights.append(lh)

        total_text_h = sum(line_heights) + (len(c_lines) - 1) * 14
        pill_pad_x = 36
        pill_pad_y = 24
        pill_w = max_line_w + pill_pad_x * 2
        pill_h = total_text_h + pill_pad_y * 2

        pill_x = (W - pill_w) // 2
        pill_y = 1140  # Fixed safe vertical position

        # Draw translucent dark pill
        pill_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(pill_layer)
        pdraw.rounded_rectangle(
            [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
            radius=24,
            fill=(10, 15, 30, 205),
            outline=(255, 215, 0, 220),
            width=3
        )
        frame = Image.alpha_composite(frame, pill_layer)
        draw = ImageDraw.Draw(frame)

        # Render vibrant yellow cartoon text with strong black outline
        cur_cy = pill_y + pill_pad_y
        for i, cl in enumerate(c_lines):
            cbb = draw.textbbox((0, 0), cl, font=cap_font)
            cx = (W - (cbb[2] - cbb[0])) // 2
            _draw_text_with_outline(
                draw, (cx, cur_cy), cl, cap_font,
                fill_color=(255, 242, 0),  # Bright golden yellow
                outline_color=(0, 0, 0),
                outline_width=5
            )
            cur_cy += line_heights[i] + 14

    # 5. Bottom Progress Bar
    progress = max(0.0, min(1.0, t / duration)) if duration > 0 else 0.0
    draw.rectangle([0, H - 12, W, H], fill=(120, 120, 120, 150))
    if progress > 0:
        draw.rectangle([0, H - 12, int(W * progress), H], fill=(255, 200, 0))

    return np.array(frame.convert("RGB"))


def _split_into_phrases(script: str, target_words: int = 5) -> list[str]:
    """Split script into short punchy 4-7 word phrases for engaging subtitles."""
    words = script.strip().split()
    phrases = []
    i = 0
    while i < len(words):
        chunk = words[i:i + target_words]
        phrases.append(" ".join(chunk))
        i += target_words
    return phrases or [script]


def _build_part_video(
    config: dict,
    title: str,
    subject: str,
    script: str,
    part_num: int,
    audio_path: str,
    bg_video_path: str | None,
    bg_image: Image.Image | None,
    colors: list,
    output_path: str
):
    """Assemble final MP4 for Part 1 or Part 2."""
    import imageio_ffmpeg
    from moviepy import AudioFileClip, VideoClip, VideoFileClip
    import moviepy.config as mconf
    mconf.FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Prepare 3D mascot image
    character_img = get_3d_character_image(subject, target_size=430)

    # Prepare background video clip if available
    bg_clip = None
    if bg_video_path and os.path.exists(bg_video_path):
        try:
            raw_bg = VideoFileClip(bg_video_path)
            # Resize / crop to 1080x1920
            w, h = raw_bg.size
            scale = max(W / w, H / h)
            scaled_w, scaled_h = int(w * scale), int(h * scale)
            bg_resized = raw_bg.resized((scaled_w, scaled_h))
            # Center crop
            x1 = (scaled_w - W) // 2
            y1 = (scaled_h - H) // 2
            bg_cropped = bg_resized.cropped(x1=x1, y1=y1, width=W, height=H)
            bg_clip = bg_cropped
            logger.info(f"Using Pexels/Veo background video clip for Part {part_num}")
        except Exception as e:
            logger.warning(f"Error loading background video ({e}), using image/gradient")
            bg_clip = None

    # Split narration into fast-paced subtitle chunks
    phrases = _split_into_phrases(script, target_words=5)
    spf = duration / len(phrases)

    category = topic_data.get("category", "").strip()
    badge_label = f"PART {part_num} • {category.upper()}" if category else f"PART {part_num} of 2"

    def make_frame(t):
        # 1. Get base frame
        if bg_clip is not None:
            t_loop = t % bg_clip.duration if bg_clip.duration > 0 else 0
            raw_frame = bg_clip.get_frame(t_loop)
            bg_img = Image.fromarray(raw_frame)
        elif bg_image is not None:
            scale = 1.0 + 0.08 * (t / duration)
            nw, nh = int(W * scale), int(H * scale)
            zoomed = bg_image.resize((nw, nh), Image.BILINEAR)
            left = (nw - W) // 2
            top = (nh - H) // 2
            bg_img = zoomed.crop((left, top, left + W, top + H))
        else:
            bg_img = _make_gradient_frame(colors, t)

        # 2. Get current phrase
        idx = min(int(t / spf), len(phrases) - 1)
        cur_phrase = phrases[idx]

        return _render_short_frame(
            bg_img, character_img, title, cur_phrase, badge_label, t, duration
        )

    clip = VideoClip(make_frame, duration=duration)
    clip = clip.with_audio(audio).with_fps(FPS)

    out_dir = os.path.dirname(output_path) or "output"
    temp_audio = os.path.join(out_dir, f"temp_snd_part_{part_num}.m4a")

    logger.info(f"Rendering Part {part_num} ({badge_label}) -> {output_path} ({duration:.1f}s)")
    clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=temp_audio,
        temp_audiofile_path=out_dir,
        remove_temp=True,
        fps=FPS,
        preset="ultrafast",
        logger=None,
    )

    audio.close()
    if bg_clip:
        bg_clip.close()
    clip.close()
    logger.info(f"Part {part_num} finished!")
    return output_path


def _prepare_part(config: dict, topic_data: dict, script: str, part_num: int, audio_path: str, output_path: str):
    """Fetch visuals and render one complete Short."""
    output_dir = config.get("output_dir", "output")
    title = topic_data.get("topic", "Fun Kids Short")
    subject = topic_data.get("subject", "star")
    category = topic_data.get("category", "kids")
    colors = topic_data.get("color_scheme", DEFAULT_PALETTES[part_num % len(DEFAULT_PALETTES)])
    video_query = topic_data.get("video_query", f"{subject} {category} cartoon cute")
    veo_prompt = topic_data.get("veo_prompt", f"A cute 3D cartoon {subject} in {category}, Disney Pixar style, 9:16 vertical")

    # 1. Try Gemini Veo AI Video Generation
    veo_video = os.path.join(output_dir, f"veo_bg_p{part_num}.mp4")
    bg_video_path = try_generate_veo_video(config, veo_prompt, veo_video)

    # 2. If Veo not available, download Pexels HD Portrait Video
    if not bg_video_path:
        pexels_vid = os.path.join(output_dir, f"pexels_bg_p{part_num}.mp4")
        bg_video_path = _download_pexels_video(config.get("pexels_api_key", ""), video_query, pexels_vid)

    # 3. If no video, fetch Pexels HD Image for Ken Burns effect
    bg_image = None
    if not bg_video_path:
        bg_image = _download_pexels_image(config.get("pexels_api_key", ""), video_query)

    return _build_part_video(
        config, title, subject, script, part_num, audio_path, bg_video_path, bg_image, colors, output_path, topic_data=topic_data
    )


def create_video_parts(config: dict, script_data: dict,
                       topic_data: dict | tuple | list, audio_paths: tuple,
                       topic2_data: dict | None = None) -> list[str]:
    """
    Generate Part 1 and Part 2 high-quality animated YouTube Shorts.
    Supports dual distinct topics for Part 1 and Part 2.
    Returns: [part1_mp4_path, part2_mp4_path]
    """
    output_dir = config.get("output_dir", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Resolve topic1 and topic2
    if isinstance(topic_data, (tuple, list)):
        t1 = topic_data[0]
        t2 = topic_data[1] if len(topic_data) > 1 else topic_data[0]
    elif topic2_data is not None:
        t1 = topic_data
        t2 = topic2_data
    else:
        t1 = topic_data
        t2 = topic_data

    p1 = os.path.join(output_dir, "part1.mp4")
    p2 = os.path.join(output_dir, "part2.mp4")

    _prepare_part(config, t1, script_data["part1_script"], 1, audio_paths[0], p1)
    _prepare_part(config, t2, script_data["part2_script"], 2, audio_paths[1], p2)

    return [p1, p2]
