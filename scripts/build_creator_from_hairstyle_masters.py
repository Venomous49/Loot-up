from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "creator_sources"
OUTPUT = ROOT / "assets" / "creator"

MASTERS = {
    "female": {
        "female_long": SOURCE / "female_long.webp",
        "female_wavy": SOURCE / "female_wavy.png",
        "female_bob": SOURCE / "female_bob.png",
        "female_ponytail": SOURCE / "female_ponytail.png",
        "female_short": SOURCE / "female_short.png",
    },
    "male": {
        "male_textured": SOURCE / "male_textured.webp",
        "male_short": SOURCE / "male_short.png",
        "male_medium": SOURCE / "male_medium.png",
        "male_undercut": SOURCE / "male_undercut.png",
        "male_slick": SOURCE / "male_slick.png",
    },
}

SIZES = {"female": (1728, 910), "male": (1086, 1448)}
SKINS = {
    "light": (222, 174, 145),
    "warm": (194, 130, 87),
    "medium": (154, 96, 62),
    "deep": (105, 64, 42),
    "dark": (66, 40, 29),
}
HAIRS = {
    "black": (24, 20, 19),
    "brown": (70, 43, 29),
    "blond": (190, 145, 83),
    "red": (136, 57, 31),
    "purple": (84, 45, 111),
}


def ellipse(xx, yy, cx, cy, rx, ry):
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1


def connected_from_seeds(mask, seeds, scale=4):
    """Keep only dark regions connected to known points inside the hairstyle."""
    h, w = mask.shape
    small = np.asarray(
        Image.fromarray(mask.astype(np.uint8) * 255, "L").resize(
            (max(1, w // scale), max(1, h // scale)), Image.Resampling.NEAREST
        )
    ) > 0
    sh, sw = small.shape
    selected = np.zeros_like(small, dtype=bool)

    for sx, sy in seeds:
        px, py = min(sw - 1, int(sx * sw)), min(sh - 1, int(sy * sh))
        candidates = np.argwhere(small)
        if candidates.size == 0:
            continue
        distances = (candidates[:, 1] - px) ** 2 + (candidates[:, 0] - py) ** 2
        start_y, start_x = candidates[int(np.argmin(distances))]
        if distances.min() > (max(sw, sh) * .055) ** 2:
            continue

        stack = [(int(start_y), int(start_x))]
        visited = np.zeros_like(small, dtype=bool)
        visited[start_y, start_x] = True
        while stack:
            cy, cx = stack.pop()
            selected[cy, cx] = True
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < sh and 0 <= nx < sw and small[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((ny, nx))

    region = Image.fromarray(selected.astype(np.uint8) * 255, "L").resize((w, h), Image.Resampling.NEAREST)
    return np.asarray(region) > 0


def foreground_mask(image, gender):
    """Segment the person so dark walls can never enter a hair colour mask."""
    original_w, original_h = image.size
    preview = ImageOps.contain(image, (512, 512), Image.Resampling.LANCZOS)
    rgb = np.asarray(preview)
    h, w = rgb.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    if gender == "female":
        rect = (int(.25 * w), 1, int(.50 * w), h - 2)
    else:
        rect = (int(.40 * w), 1, int(.40 * w), h - 2)
    background = np.zeros((1, 65), np.float64)
    foreground = np.zeros((1, 65), np.float64)
    cv2.grabCut(rgb, mask, rect, background, foreground, 5, cv2.GC_INIT_WITH_RECT)
    person = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    person = Image.fromarray(person, "L").resize((original_w, original_h), Image.Resampling.BILINEAR)
    return np.asarray(person) > 96


def masks(image, gender, style):
    rgb = np.asarray(image).astype(np.float32)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    person = foreground_mask(image, gender)

    # Existing hair is dark and neutral/warm. Curved, style-specific geometry
    # prevents dark alley pixels from being recoloured with the hair.
    warm_or_black = (r > g * 1.045) | ((r < 45) & (g < 42) & (b < 40))
    dark_hair = (r < 125) & (g < 108) & (b < 104) & (r >= b * .82) & warm_or_black
    if gender == "female":
        face = ellipse(x, y, .52, .285, .092, .185)
        cap = ellipse(x, y, .52, .205, .135, .205)
        geometry = {
            "female_long": cap | ellipse(x, y, .425, .50, .105, .39) | ellipse(x, y, .615, .50, .105, .39),
            "female_wavy": cap | ellipse(x, y, .405, .51, .115, .40) | ellipse(x, y, .635, .51, .115, .40),
            "female_bob": ellipse(x, y, .52, .245, .155, .245),
            "female_ponytail": cap | ellipse(x, y, .52, .075, .080, .070) | ellipse(x, y, .625, .30, .050, .22),
            "female_short": ellipse(x, y, .52, .175, .120, .135),
        }[style]
        seeds = {
            "female_long": [(.52, .07)],
            "female_wavy": [(.52, .07)],
            "female_bob": [(.52, .07)],
            "female_ponytail": [(.52, .05)],
            "female_short": [(.52, .07)],
        }[style]
        base_candidate = dark_hair & geometry & ~face
        connected = connected_from_seeds(base_candidate, seeds)
        candidate = connected & person
        if candidate.sum() < 300:
            candidate = connected
        hair = candidate
        anatomy = face | ((x > .46) & (x < .58) & (y > .39) & (y < .60))
    else:
        face = ellipse(x, y, .585, .145, .070, .070)
        geometry = {
            "male_textured": ellipse(x, y, .585, .088, .060, .058),
            "male_short": ellipse(x, y, .585, .095, .062, .050),
            "male_medium": ellipse(x, y, .585, .103, .085, .078),
            "male_undercut": ellipse(x, y, .585, .090, .082, .070),
            "male_slick": ellipse(x, y, .585, .090, .075, .062),
        }[style]
        base_candidate = dark_hair & geometry & ~face
        candidate = base_candidate & person
        if candidate.sum() < 180:
            candidate = base_candidate
        hair = candidate
        anatomy = face | ((x > .52) & (x < .65) & (y > .17) & (y < .31))
        anatomy |= ((x > .39) & (x < .76) & (y > .25) & (y < .72))

    skin_colour = (r > g * 1.05) & (g > b * 1.04) & (r > 48) & (b < 185)
    skin = skin_colour & anatomy & person

    def soften(mask, radius):
        layer = Image.fromarray((mask.astype(np.uint8) * 255), "L")
        return np.asarray(layer.filter(ImageFilter.GaussianBlur(radius))) / 255.0

    return soften(hair, 1.4), soften(skin, 2.0)


def tint(rgb, alpha, target, strength, minimum_luminance=.35):
    src = rgb.astype(np.float32)
    luminance = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    target = np.asarray(target, dtype=np.float32)
    coloured = target[None, None, :] * np.clip(luminance[..., None] / 105.0, minimum_luminance, 1.75)
    a = (alpha * strength)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255)


def build():
    written = 0
    for gender, styles in MASTERS.items():
        for style, source in styles.items():
            if not source.exists():
                raise SystemExit(f"Missing hairstyle master: {source}")
            master = Image.open(source).convert("RGB")
            master = ImageOps.fit(master, SIZES[gender], Image.Resampling.LANCZOS)
            base = np.asarray(master).astype(np.float32)
            hair_mask, skin_mask = masks(master, gender, style)
            if hair_mask.sum() < 250:
                raise SystemExit(f"Unsafe hair mask for {gender}/{style}")

            for skin_name, skin_rgb in SKINS.items():
                skinned = tint(base, skin_mask, skin_rgb, .78)
                for hair_name, hair_rgb in HAIRS.items():
                    hair_floor = .35
                    if hair_name == "purple":
                        dark_styles = {"female_ponytail", "female_short", "male_textured", "male_short", "male_undercut"}
                        hair_floor = .62 if style in dark_styles else .40
                    result = tint(skinned, hair_mask, hair_rgb, 1.0, hair_floor).astype(np.uint8)
                    path = OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(result, "RGB").save(path, "WEBP", quality=91, method=6)
                    written += 1

    if written != 250:
        raise SystemExit(f"Expected 250 presets, wrote {written}")
    print(f"Built {written} presets from ten distinct hairstyle masters")


if __name__ == "__main__":
    build()
