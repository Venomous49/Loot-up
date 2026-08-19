from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "creator_sources"
OUTPUT = ROOT / "assets" / "creator"
BACKGROUND = SOURCE / "creator_background_master.png"
MASKS = SOURCE / "person_masks"
BACKGROUND_CACHE = None

MASTERS = {
    "female": {
        "female_long": SOURCE / "female_long.webp",
        "female_wavy": SOURCE / "female_wavy.png",
        "female_bob": SOURCE / "female_bob.png",
        "female_ponytail": SOURCE / "female_ponytail.png",
        "female_short": SOURCE / "female_short.png",
    },
    "male": {
        "male_textured": SOURCE / "male_textured_clean.png",
        "male_short": SOURCE / "male_short_clean.png",
        "male_medium": SOURCE / "male_medium_clean.png",
        "male_undercut": SOURCE / "male_undercut_clean.png",
        "male_slick": SOURCE / "male_slick_clean.png",
    },
}

COLOR_MASTERS = {
    ("female_long", "brown"): SOURCE / "female_long_brown_natural.png",
    ("female_long", "blond"): SOURCE / "female_long_blond_natural.png",
    ("female_long", "red"): SOURCE / "female_long_red_natural.png",
    ("female_long", "purple"): SOURCE / "female_long_purple_natural.png",
    ("female_wavy", "blond"): SOURCE / "female_wavy_blond_natural.png",
    ("female_wavy", "red"): SOURCE / "female_wavy_red_natural.png",
    ("female_wavy", "purple"): SOURCE / "female_wavy_purple_natural.png",
    ("female_bob", "brown"): SOURCE / "female_bob_brown_natural.png",
    ("female_bob", "blond"): SOURCE / "female_bob_blond_natural.png",
    ("female_bob", "red"): SOURCE / "female_bob_red_natural.png",
    ("female_bob", "purple"): SOURCE / "female_bob_purple_natural.png",
    ("female_ponytail", "brown"): SOURCE / "female_ponytail_brown_natural.png",
    ("female_ponytail", "blond"): SOURCE / "female_ponytail_blond_natural.png",
    ("female_ponytail", "red"): SOURCE / "female_ponytail_red_natural.png",
    ("female_ponytail", "purple"): SOURCE / "female_ponytail_purple_natural.png",
    ("female_short", "brown"): SOURCE / "female_short_brown_natural.png",
    ("female_short", "blond"): SOURCE / "female_short_blond_natural.png",
    ("female_short", "red"): SOURCE / "female_short_red_natural.png",
    ("female_short", "purple"): SOURCE / "female_short_purple_natural.png",
    ("male_textured", "brown"): SOURCE / "male_textured_brown_natural.png",
    ("male_textured", "blond"): SOURCE / "male_textured_blond_natural.png",
    ("male_textured", "red"): SOURCE / "male_textured_red_natural.png",
    ("male_textured", "purple"): SOURCE / "male_textured_purple_natural.png",
    ("male_short", "brown"): SOURCE / "male_short_brown_natural.png",
    ("male_short", "blond"): SOURCE / "male_short_blond_natural.png",
    ("male_short", "red"): SOURCE / "male_short_red_natural.png",
    ("male_short", "purple"): SOURCE / "male_short_purple_natural.png",
    ("male_medium", "brown"): SOURCE / "male_medium_brown_natural.png",
    ("male_medium", "blond"): SOURCE / "male_medium_blond_natural.png",
    ("male_medium", "red"): SOURCE / "male_medium_red_natural.png",
    ("male_medium", "purple"): SOURCE / "male_medium_purple_natural.png",
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
    "brown": (64, 45, 35),
    "blond": (145, 116, 78),
    "red": (108, 55, 38),
    "purple": (68, 43, 82),
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
            "female_ponytail": (
                cap
                | ellipse(x, y, .52, .075, .080, .070)
                | ellipse(x, y, .625, .30, .050, .22)
                | ellipse(x, y, .430, .43, .075, .34)
                | ellipse(x, y, .610, .43, .075, .34)
            ),
            "female_short": ellipse(x, y, .52, .175, .120, .135),
        }[style]
        seeds = {
            "female_long": [(.52, .07)],
            "female_wavy": [(.52, .07)],
            "female_bob": [(.52, .07)],
            "female_ponytail": [(.52, .05)],
            "female_short": [(.52, .07)],
        }[style]
        hair_face = ellipse(x, y, .52, .285, .060, .145)
        neck_and_chest = ellipse(x, y, .52, .48, .075, .20)
        base_candidate = dark_hair & geometry & ~hair_face & ~neck_and_chest
        connected = connected_from_seeds(base_candidate, seeds)
        if style == "female_ponytail":
            candidate = base_candidate & person
        else:
            candidate = connected & person
            if candidate.sum() < 300:
                candidate = connected
        hair = candidate
        anatomy = face | ((x > .46) & (x < .58) & (y > .39) & (y < .60))
    else:
        head = {
            "male_textured": (.625, .092, .070, .065),
            "male_short": (.610, .092, .075, .060),
            "male_medium": (.625, .105, .092, .082),
            "male_undercut": (.640, .092, .088, .073),
            "male_slick": (.650, .092, .082, .067),
        }[style]
        hx, hy, hrx, hry = head
        face = ellipse(x, y, hx, hy + .070, hrx * .90, .075)
        geometry = {
            "male_textured": ellipse(x, y, hx, hy, hrx, hry),
            "male_short": ellipse(x, y, hx, hy, hrx, hry),
            "male_medium": ellipse(x, y, hx, hy, hrx, hry),
            "male_undercut": ellipse(x, y, hx, hy, hrx, hry),
            "male_slick": ellipse(x, y, hx, hy, hrx, hry),
        }[style]
        # Male foreheads can share the warm/dark range of the hair source.
        # Require neutral-dark pixels so skin can never become a coloured band.
        neutral_dark_hair = (
            (r < 118)
            & (g < 108)
            & (b < 104)
            & (((r - g) < 18) | (r < 72))
        )
        if style == "male_short":
            base_candidate = geometry & ~face & person
        else:
            base_candidate = neutral_dark_hair & geometry & ~face
        candidate = base_candidate & person
        if candidate.sum() < 180:
            candidate = base_candidate
        hair = candidate
        anatomy = face | ((x > hx - .07) & (x < hx + .07) & (y > hy + .10) & (y < hy + .27))
        anatomy |= ((x > hx - .20) & (x < hx + .20) & (y > hy + .18) & (y < hy + .62))

    skin_colour = (r > g * 1.05) & (g > b * 1.04) & (r > 48) & (b < 185)
    skin = skin_colour & anatomy & person

    def soften(mask, radius):
        layer = Image.fromarray((mask.astype(np.uint8) * 255), "L")
        return np.asarray(layer.filter(ImageFilter.GaussianBlur(radius))) / 255.0

    hair_alpha = soften(hair, 1.4)
    if style in {"female_long", "female_wavy"}:
        # The source hood contains dark warm folds directly connected to the
        # hair. Fade the lower mask before it reaches the clothing so vivid
        # colours cannot paint a solid block over the chest and shoulders.
        lower_fade = np.clip((.82 - y) / .22, 0, 1)
        hair_alpha *= lower_fade

    return hair_alpha, soften(skin, 2.0)


def tint(rgb, alpha, target, strength, minimum_luminance=.35, preserve_texture=False, maximum_luminance=1.08):
    src = rgb.astype(np.float32)
    luminance = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    target = np.asarray(target, dtype=np.float32)
    selected = luminance[alpha > .35]
    low, high = (np.percentile(selected, (8, 94)) if selected.size else (20.0, 130.0))
    span = max(28.0, float(high - low))
    # Map the full tonal range of the actual hairstyle to the target colour.
    # This retains individual strands instead of painting a flat opaque shape.
    normalized = np.clip(((luminance - low) / span)[..., None], 0, 1)
    if preserve_texture:
        brightness = minimum_luminance + (maximum_luminance - minimum_luminance) * normalized
    else:
        brightness = np.clip(normalized, minimum_luminance, 1.75)
    coloured = target[None, None, :] * np.clip(brightness, 0, 1.75)
    a = (alpha * strength)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255)


def tint_skin(rgb, alpha, target):
    """Apply an even complexion while retaining restrained photographic shading."""
    src = rgb.astype(np.float32)
    target = np.asarray(target, dtype=np.float32)
    luminance = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    skin_pixels = luminance[alpha > .45]
    midpoint = float(np.median(skin_pixels)) if skin_pixels.size else 105.0
    # Compress source contrast so a naturally shadowed source cannot turn into
    # a dark patch after selecting a deeper complexion.
    relative = np.clip((luminance - midpoint) / 255.0, -.16, .16)
    coloured = np.clip(target[None, None, :] + relative[..., None] * 92.0, 0, 255)
    # Preserve most of the original micro-contrast; a heavy replacement makes
    # facial detail look airbrushed and exaggerates source-side shadows.
    # Make the five requested complexions visibly distinct on every master.
    # The compressed luminance above keeps this stronger blend from creating
    # the forehead/cheek shadow patches present in the previous assets.
    a = (alpha * .76)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255)


def standardized_override_skin_mask(image, gender):
    """Skin mask for colour masters that already use the standardized layout."""
    rgb = np.asarray(image).astype(np.float32)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    if gender == "male":
        anatomy = ellipse(x, y, .665, .255, .075, .145)
        anatomy |= ellipse(x, y, .665, .405, .050, .090)
    else:
        anatomy = ellipse(x, y, .520, .285, .092, .185)
        anatomy |= ellipse(x, y, .520, .480, .070, .120)
    skin_colour = (r > g * 1.015) & (g > b * .98) & (r > 40) & (b < 205)
    return np.asarray(
        Image.fromarray(((skin_colour & anatomy).astype(np.uint8) * 255), "L")
        .filter(ImageFilter.GaussianBlur(2.0))
    ) / 255.0


def composite_on_master_background(output, gender, style):
    """Use reviewed masks only; every style gets an identical scene and layout."""
    global BACKGROUND_CACHE
    canvas_size = (1728, 910)
    portrait = ImageOps.fit(output.convert("RGB"), canvas_size, Image.Resampling.LANCZOS)
    mask_path = MASKS / f"{style}.png"
    if not mask_path.exists():
        raise SystemExit(f"Missing reviewed person mask: {mask_path}")
    alpha = Image.open(mask_path).convert("L")
    if alpha.size != canvas_size:
        raise SystemExit(f"Unexpected mask size for {style}: {alpha.size}")
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit(f"Empty person mask: {style}")

    cutout = portrait.crop(bbox)
    cutout_alpha = alpha.crop(bbox)
    target_box = {
        "male": (764, 46, 1412, 910),
        "female": (455, 22, 1345, 910),
    }[gender]
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    cutout = cutout.resize(target_size, Image.Resampling.LANCZOS)
    cutout_alpha = cutout_alpha.resize(target_size, Image.Resampling.LANCZOS)

    if BACKGROUND_CACHE is None:
        BACKGROUND_CACHE = ImageOps.fit(
            Image.open(BACKGROUND).convert("RGB"),
            canvas_size,
            Image.Resampling.LANCZOS,
        ).filter(ImageFilter.UnsharpMask(radius=.7, percent=40, threshold=4))
    canvas = BACKGROUND_CACHE.copy()
    canvas.paste(cutout, target_box[:2], cutout_alpha)
    return canvas


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

            color_bases = {}
            for (override_style, hair_name), override_source in COLOR_MASTERS.items():
                if override_style != style:
                    continue
                override = Image.open(override_source).convert("RGB")
                # Reviewed colour masters are already complete standardized
                # 1728x910 scenes. Never force male masters through the old
                # portrait canvas (1086x1448), which zoomed and cropped them.
                override = ImageOps.fit(override, (1728, 910), Image.Resampling.LANCZOS)
                override_base = np.asarray(override).astype(np.float32)
                override_skin_mask = standardized_override_skin_mask(override, gender)
                color_bases[hair_name] = (override_base, override_skin_mask)

            for skin_name, skin_rgb in SKINS.items():
                skinned = tint_skin(base, skin_mask, skin_rgb)
                for hair_name, hair_rgb in HAIRS.items():
                    is_color_master = hair_name in color_bases
                    if is_color_master:
                        override_base, override_skin_mask = color_bases[hair_name]
                        result = tint_skin(override_base, override_skin_mask, skin_rgb).astype(np.uint8)
                    else:
                        hair_floor = .35
                        if gender == "female":
                            hair_floor = {
                                "black": .24,
                                "brown": .34,
                                "blond": .68,
                                "red": .48,
                                "purple": .20,
                            }[hair_name]
                        elif hair_name == "purple":
                            dark_styles = {"male_textured", "male_short", "male_undercut"}
                            if style in dark_styles:
                                hair_floor = .62
                            else:
                                hair_floor = .40
                        hair_strength = {
                            "black": 0.0,
                            "brown": .46,
                            "blond": .64,
                            "red": .58,
                            "purple": .56,
                        }[hair_name]
                        hair_ceiling = {
                            "black": .84,
                            "brown": .94,
                            "blond": .94,
                            "red": .96,
                            "purple": .92,
                        }[hair_name]
                        result = tint(
                            skinned,
                            hair_mask,
                            hair_rgb,
                            hair_strength,
                            hair_floor,
                            True,
                            hair_ceiling,
                        ).astype(np.uint8)
                    path = OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    output = Image.fromarray(result, "RGB")
                    if is_color_master:
                        # Background and person placement are already final.
                        output = output.filter(ImageFilter.UnsharpMask(radius=.65, percent=55, threshold=3))
                    elif gender == "male":
                        crop_height = round(output.width * 910 / 1728)
                        output = output.crop((0, 0, output.width, crop_height)).resize((1728, 910), Image.Resampling.LANCZOS)
                        output = output.filter(ImageFilter.UnsharpMask(radius=.8, percent=70, threshold=3))
                    else:
                        output = output.filter(ImageFilter.UnsharpMask(radius=.65, percent=55, threshold=3))
                    if not is_color_master:
                        output = composite_on_master_background(output, gender, style)
                    output.save(path, "WEBP", quality=91, method=6)
                    written += 1

    if written != 250:
        raise SystemExit(f"Expected 250 presets, wrote {written}")
    print(f"Built {written} presets from ten distinct hairstyle masters")


if __name__ == "__main__":
    build()
