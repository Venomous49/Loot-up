from pathlib import Path
import os

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "creator_sources"
OUTPUT = ROOT / "assets" / "creator"
BACKGROUND = SOURCE / "creator_background_master.png"
MASKS = SOURCE / "person_masks"
COLOR_MASKS = SOURCE / "color_master_masks"
STANDARDIZED = SOURCE / "standardized_black"
FACE_MODEL = SOURCE / "face_detection_yunet_2023mar.onnx"
BACKGROUND_CACHE = None

MASTERS = {
    "female": {
        # The short style is the clean torso master: it contains no long lock
        # that can be copied into another hairstyle by the body invariant.
        "female_short": STANDARDIZED / "female_short.webp",
        "female_long": STANDARDIZED / "female_long.webp",
        "female_wavy": STANDARDIZED / "female_wavy.webp",
        "female_bob": STANDARDIZED / "female_bob.webp",
        "female_ponytail": STANDARDIZED / "female_ponytail.webp",
    },
    "male": {
        "male_textured": STANDARDIZED / "male_textured.webp",
        "male_short": STANDARDIZED / "male_short.webp",
        "male_medium": STANDARDIZED / "male_medium.webp",
        "male_undercut": STANDARDIZED / "male_undercut.webp",
        "male_slick": STANDARDIZED / "male_slick.webp",
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
TARGET_FACES = {
    "male": (914.0, 160.0, 180.0, 235.0),
    "female": (800.0, 125.0, 212.0, 304.0),
}
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


def detect_face(image):
    """Return the highest-confidence YuNet face box as x, y, width, height."""
    if not FACE_MODEL.exists():
        raise SystemExit(f"Missing face detector: {FACE_MODEL}")
    bgr = cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2BGR)
    detector = cv2.FaceDetectorYN.create(
        str(FACE_MODEL), "", (bgr.shape[1], bgr.shape[0]), .64, .3, 5000
    )
    _, faces = detector.detect(bgr)
    if faces is None or len(faces) == 0:
        raise SystemExit("No face detected in creator master")
    face = max(faces, key=lambda row: row[-1])
    return tuple(float(value) for value in face[:4])


def masks(image, gender, style):
    rgb = np.asarray(image).astype(np.float32)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    reviewed_mask = MASKS / f"{style}.png"
    if reviewed_mask.exists():
        person_layer = ImageOps.fit(
            Image.open(reviewed_mask).convert("L"), (w, h), Image.Resampling.LANCZOS
        )
        person = np.asarray(person_layer) > 24
    else:
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
        # Cover every visible complexion area, including the open neckline and
        # forearm.  Pixel classification below keeps fabric out; these bounds
        # only prevent the alley/background from entering the mask.
        neckline = np.zeros((h, w), np.uint8)
        cv2.fillPoly(
            neckline,
            [np.array([
                [.475 * w, .39 * h], [.565 * w, .39 * h],
                [.585 * w, .50 * h], [.555 * w, .585 * h],
                [.520 * w, .620 * h], [.485 * w, .585 * h],
                [.455 * w, .50 * h],
            ], np.int32)],
            1,
        )
        anatomy = face | (neckline > 0)
        anatomy |= ((x > .690) & (x < .835) & (y > .58) & (y < .995))
    else:
        fx, fy, fw, fh = detect_face(image)
        hx, hy = (fx + fw * .50) / w, (fy - fh * .04) / h
        hrx, hry = fw * .68 / w, fh * .55 / h
        face = ellipse(x, y, (fx + fw * .5) / w, (fy + fh * .52) / h, fw * .47 / w, fh * .52 / h)
        geometry = ellipse(x, y, hx, hy, hrx, hry)
        # Male foreheads can share the warm/dark range of the hair source.
        # Require neutral-dark pixels so skin can never become a coloured band.
        neutral_dark_hair = (
            (r < 118)
            & (g < 108)
            & (b < 104)
            & (((r - g) < 18) | (r < 72))
        )
        if style in {"male_short", "male_undercut", "male_slick"}:
            skin_like = (r > g * 1.03) & (g > b * 1.01) & (r > 70)
            base_candidate = geometry & ~face & ~skin_like & person
        else:
            base_candidate = neutral_dark_hair & geometry & ~face
        candidate = base_candidate & person
        if candidate.sum() < 180:
            candidate = base_candidate
        hair = candidate
        anatomy = face | ((x > hx - .07) & (x < hx + .07) & (y > hy + .10) & (y < hy + .30))

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

    skin_alpha = soften(skin, 1.15)
    # Never let Gaussian feathering paint an oval outside actual skin.  A
    # small dilation admits antialiased edge pixels but prevents face/neck
    # halos and mismatched patches over hair or clothing.
    skin_guard = cv2.dilate(skin.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1) > 0
    skin_alpha *= skin_guard
    return hair_alpha, skin_alpha


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


def tint_skin(rgb, alpha, target, strength=.76):
    """Apply an even complexion while retaining restrained photographic shading."""
    src = rgb.astype(np.float32)
    target = np.asarray(target, dtype=np.float32)
    luminance = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    skin_pixels = luminance[alpha > .45]
    midpoint = float(np.median(skin_pixels)) if skin_pixels.size else 105.0
    # Compress source contrast so a naturally shadowed source cannot turn into
    # a dark patch after selecting a deeper complexion.
    # Only retain fine local modelling.  The older wide +/- .16 range carried
    # the source key-light shadow into deep/dark variants as charcoal patches.
    relative = np.clip((luminance - midpoint) / 255.0, -.075, .075)
    coloured = np.clip(target[None, None, :] + relative[..., None] * 92.0, 0, 255)
    # Preserve most of the original micro-contrast; a heavy replacement makes
    # facial detail look airbrushed and exaggerates source-side shadows.
    # Make the five requested complexions visibly distinct on every master.
    # The compressed luminance above keeps this stronger blend from creating
    # the forehead/cheek shadow patches present in the previous assets.
    a = (alpha * strength)[..., None]
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
        anatomy = ellipse(x, y, .520, .285, .105, .195)
        neckline = np.zeros((h, w), np.uint8)
        cv2.fillPoly(
            neckline,
            [np.array([
                [.475 * w, .39 * h], [.565 * w, .39 * h],
                [.585 * w, .50 * h], [.555 * w, .585 * h],
                [.520 * w, .620 * h], [.485 * w, .585 * h],
                [.455 * w, .50 * h],
            ], np.int32)],
            1,
        )
        anatomy |= neckline > 0
        anatomy |= ((x > .690) & (x < .835) & (y > .58) & (y < .995))
    skin_colour = (r > g * 1.015) & (g > b * .98) & (r > 40) & (b < 205)
    raw = skin_colour & anatomy
    softened = np.asarray(
        Image.fromarray(((skin_colour & anatomy).astype(np.uint8) * 255), "L")
        .filter(ImageFilter.GaussianBlur(1.15))
    ) / 255.0
    guard = cv2.dilate(raw.astype(np.uint8), np.ones((5, 5), np.uint8), iterations=1) > 0
    return softened * guard


def composite_on_master_background(output, gender, style, mask_path=None):
    """Place each person on the shared set without ever stretching a face."""
    global BACKGROUND_CACHE
    canvas_size = (1728, 910)
    portrait = ImageOps.fit(output.convert("RGB"), canvas_size, Image.Resampling.LANCZOS)
    mask_path = mask_path or (MASKS / f"{style}.png")
    if not mask_path.exists():
        raise SystemExit(f"Missing reviewed person mask: {mask_path}")
    alpha = Image.open(mask_path).convert("L")
    if alpha.size != canvas_size:
        alpha = ImageOps.fit(alpha, canvas_size, Image.Resampling.LANCZOS)
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit(f"Empty person mask: {style}")

    original_cutout = portrait.crop(bbox)
    original_alpha = alpha.crop(bbox)
    face_x, face_y, face_w, face_h = detect_face(portrait)
    target_x, target_y, target_w, target_h = TARGET_FACES[gender]
    fixed_center_x = target_x + target_w / 2
    anchor_center_x = fixed_center_x
    desired_y = target_y
    # A single scale is essential: independent X/Y correction was changing
    # jaw width and face length when the user switched hairstyles.
    scale = target_h / face_h
    if BACKGROUND_CACHE is None:
        BACKGROUND_CACHE = ImageOps.fit(
            Image.open(BACKGROUND).convert("RGB"),
            canvas_size,
            Image.Resampling.LANCZOS,
        ).filter(ImageFilter.UnsharpMask(radius=.7, percent=40, threshold=4))
    canvas = None
    for attempt in range(3):
        target_size = (
            max(1, round((bbox[2] - bbox[0]) * scale)),
            max(1, round((bbox[3] - bbox[1]) * scale)),
        )
        cutout = original_cutout.resize(target_size, Image.Resampling.LANCZOS)
        cutout_alpha = original_alpha.resize(target_size, Image.Resampling.LANCZOS)
        paste_at = (
            round(anchor_center_x - (face_x + face_w / 2 - bbox[0]) * scale),
            round(target_y - (face_y - bbox[1]) * scale),
        )
        canvas = BACKGROUND_CACHE.copy()
        canvas.paste(cutout, paste_at, cutout_alpha)
        if attempt < 2:
            final_x, final_y, final_w, final_h = detect_face(canvas)
            scale *= target_h / final_h
            # Compensate detector shifts while retaining one uniform scale.
            anchor_center_x += fixed_center_x - (final_x + final_w / 2)
            target_y += target_y - final_y
    # Final translation does not alter face proportions; it only locks the
    # detected top-left corner to the shared reference position.
    final_x, final_y, final_w, _ = detect_face(canvas)
    shift = (
        round(fixed_center_x - (final_x + final_w / 2)),
        round(desired_y - final_y),
    )
    if shift != (0, 0):
        canvas = BACKGROUND_CACHE.copy()
        canvas.paste(
            cutout,
            (paste_at[0] + shift[0], paste_at[1] + shift[1]),
            cutout_alpha,
        )
    return canvas


def build():
    written = 0
    for gender, styles in MASTERS.items():
        requested_gender = os.environ.get("CREATOR_BUILD_GENDER")
        if requested_gender and gender != requested_gender:
            continue
        for style, source in styles.items():
            if not source.exists():
                raise SystemExit(f"Missing hairstyle master: {source}")
            master = Image.open(source).convert("RGB")
            master = ImageOps.fit(master, (1728, 910), Image.Resampling.LANCZOS)
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
                override_mask = COLOR_MASKS / override_source.with_suffix(".png").name
                if not override_mask.exists():
                    raise SystemExit(f"Missing colour-master person mask: {override_mask}")
                color_bases[hair_name] = (override_base, override_skin_mask, override_mask)

            for skin_name, skin_rgb in SKINS.items():
                # Keep pores, eyes and facial contours visible in the enlarged
                # profile card. Higher replacement strengths flattened these
                # details even though the creator thumbnail looked acceptable.
                # Preserve real source texture and lighting.  Higher strengths
                # made the light female complexion look printed/airbrushed.
                skin_strength = .50 if gender == "female" else .60
                skinned = tint_skin(base, skin_mask, skin_rgb, strength=skin_strength)
                for hair_name, hair_rgb in HAIRS.items():
                    is_color_master = hair_name in color_bases
                    if is_color_master:
                        override_base, override_skin_mask, override_mask = color_bases[hair_name]
                        result = tint_skin(
                            override_base,
                            override_skin_mask,
                            skin_rgb,
                            strength=skin_strength,
                        ).astype(np.uint8)
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
                            # Fade/undercut and slick/back styles used to read as
                            # black. Keep a restrained violet in their highlights.
                            hair_floor = .58 if style in {"male_short", "male_undercut", "male_slick"} else .52
                        hair_strength = {
                            "black": 0.0,
                            "brown": .46,
                            "blond": .64,
                            "red": .58,
                            "purple": .72,
                        }[hair_name]
                        hair_ceiling = {
                            "black": .84,
                            "brown": .94,
                            "blond": .94,
                            "red": .96,
                            "purple": 1.02,
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
                    output = composite_on_master_background(
                        output,
                        gender,
                        style,
                        override_mask if is_color_master else None,
                    )
                    # Keep every source face intact. Pasting a shared inner
                    # face caused blurred brows and a shortened jaw in the
                    # enlarged profile card even when thumbnails looked fine.
                    output = output.filter(
                        ImageFilter.UnsharpMask(radius=.55, percent=38, threshold=3)
                    )
                    output.save(path, "WEBP", quality=95, method=6)
                    written += 1

    expected = 125 if os.environ.get("CREATOR_BUILD_GENDER") else 250
    if written != expected:
        raise SystemExit(f"Expected {expected} presets, wrote {written}")
    print(f"Built {written} presets from ten distinct hairstyle masters")


if __name__ == "__main__":
    build()
