"""
character_manager.py - Loads and manages high-quality 3D cartoon characters/mascots
from the Microsoft Fluent 3D Emoji library (1,500+ Pixar/Disney style 3D assets).
Eliminates missing font glyphs (broken boxes) and gives kids a fun visual host.
"""
import os
import json
import logging
import requests
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets_cache")
TREE_FILE = os.path.join(os.path.dirname(__file__), "fluent_tree.json")


def _find_best_match(subject: str, tree: dict) -> str:
    """Find the best 3D asset path matching the topic subject."""
    sub = subject.lower().strip().replace("-", " ")

    # 1. Exact match
    if sub in tree:
        return tree[sub]

    # 2. Singular form if ends with 's' (e.g. giraffes -> giraffe)
    if sub.endswith("s") and sub[:-1] in tree:
        return tree[sub[:-1]]
    if sub.endswith("es") and sub[:-2] in tree:
        return tree[sub[:-2]]

    # 3. Word token match
    for name, path in tree.items():
        if sub in name.split():
            return path

    # 4. Substring match
    for name, path in tree.items():
        if sub in name or name in sub:
            return path

    # Fallback to cheerful friendly stars
    return tree.get("sparkles", "assets/Sparkles/3D/sparkles_3d.png")


def get_3d_character_image(subject: str, target_size: int = 420) -> Image.Image:
    """
    Download/load a transparent 3D cartoon mascot image for the subject.
    Returns RGBA Image with a soft glowing cartoon drop aura.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    tree = {}
    if os.path.exists(TREE_FILE):
        try:
            with open(TREE_FILE, "r", encoding="utf-8") as f:
                tree = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read fluent_tree.json: {e}")

    rel_path = _find_best_match(subject, tree)
    filename = os.path.basename(rel_path)
    cached_path = os.path.join(CACHE_DIR, filename)

    if not os.path.exists(cached_path) or os.path.getsize(cached_path) == 0:
        url = f"https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/{rel_path}"
        logger.info(f"Downloading 3D mascot from: {url}")
        try:
            resp = requests.get(url, timeout=12)
            if resp.status_code == 200:
                with open(cached_path, "wb") as fh:
                    fh.write(resp.content)
            else:
                logger.warning(f"Download failed ({resp.status_code}), using fallback")
        except Exception as e:
            logger.warning(f"Error downloading mascot: {e}")

    if os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
        base_img = Image.open(cached_path).convert("RGBA")
    else:
        # Fallback cartoon star if offline/error
        base_img = Image.new("RGBA", (256, 256), (255, 215, 0, 255))

    # Resize with high quality Lanczos filter
    resized = base_img.resize((target_size, target_size), Image.LANCZOS)

    # Add soft glowing cartoon shadow behind the character
    pad = 50
    canvas_w = target_size + pad * 2
    canvas_h = target_size + pad * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Create dark silhouette for soft shadow
    shadow_mask = resized.split()[3]
    shadow = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 160))
    shadow.putalpha(shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))

    canvas.paste(shadow, (pad, pad + 12), shadow)
    canvas.paste(resized, (pad, pad), resized)

    return canvas
