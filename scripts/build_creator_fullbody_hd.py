from pathlib import Path
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_from_hairstyle_masters as base

CANVAS_SIZE = (1728, 910)
CENTER_X = CANVAS_SIZE[0] // 2
GROUND_Y = 900
TARGET_PERSON_HEIGHT = 780
WEBP_QUALITY = 98

CANONICAL = {
    "male": (base.SOURCE / "male_undercut_clean.png", "male_undercut"),
    "female": (base.SOURCE / "female_short.png", "female_short"),
}

STYLE_SOURCES = {
    "male": {
        "male_textured": base.SOURCE / "male_textured_clean.png",
        "male_short": base.SOURCE / "male_short_clean.png",
        "male_medium": base.SOURCE / "male_medium_clean.png",
        "male_undercut": base.SOURCE / "male_undercut_clean.png",
        "male_slick": base.SOURCE / "male_slick_clean.png",
    },
    "female": {
        "female_long": base.SOURCE / "female_long.webp",
        "female_wavy": base.SOURCE / "female_wavy.png",
        "female_bob": base.SOURCE / "female_bob.png",
        "female_ponytail": base.SOURCE / "female_ponytail.png",
        "female_short": base.SOURCE / "female_short.png",
    },
}

HAIR_ENVELOPES = {
    "male_textured": (190, 155, 126),
    "male_short": (165, 125, 132),
    "male_medium": (215, 185, 120),
    "male_undercut": (190, 155, 126),
    "male_slick": (185, 145, 126),
    "female_long": (300, 355, 122),
    "female_wavy": (320, 370, 118),
    "female_bob": (245, 235, 122),
    "female_ponytail": (275, 320, 112),
    "female_short": (205, 175, 126),
}

BACKGROUND = ImageOps.fit(
    Image.open(base.BACKGROUND).convert("RGB"), CANVAS_SIZE, Image.Resampling.LANCZOS
)


def fit_scene(path):
    if not path.exists():
        raise SystemExit(f"Missing creator source: {path}")
    return ImageOps.fit(Image.open(path).convert("RGB"), CANVAS_SIZE, Image.Resampling.LANCZOS)


def reviewed_mask(style):
    path = base.MASKS / f"{style}.png"
    if not path.exists():
        raise SystemExit(f"Missing reviewed creator mask: {path}")
    return ImageOps.fit(Image.open(path).convert("L"), CANVAS_SIZE, Image.Resampling.LANCZOS)


def photographic_skin_mask(scene, person_alpha):
    rgb = np.asarray(scene, dtype=np.uint8)
    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    # Broad photographic skin locus, constrained strictly to the reviewed body
    # silhouette.  The morphology closes tiny gaps so face/neck/arms tint as one
    # continuous surface instead of separate patches.
    raw = (cr >= 126) & (cr <= 184) & (cb >= 72) & (cb <= 142) & (y >= 28)
    raw &= person_alpha > 28
    layer = (raw.astype(np.uint8) * 255)
    layer = cv2.morphologyEx(layer, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    layer = cv2.morphologyEx(layer, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    layer = cv2.GaussianBlur(layer, (0, 0), 1.15)
    return layer.astype(np.float32) / 255.0


def canonical_body(gender):
    path, style = CANONICAL[gender]
    scene = fit_scene(path)
    alpha = reviewed_mask(style)
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit(f"Empty canonical mask: {gender}")

    source_person_alpha = np.asarray(alpha, dtype=np.uint8)
    source_skin = photographic_skin_mask(scene, source_person_alpha)

    cutout = scene.crop(bbox)
    cutout_alpha = alpha.crop(bbox)
    skin_crop = Image.fromarray(np.clip(source_skin * 255, 0, 255).astype(np.uint8), "L").crop(bbox)

    scale = TARGET_PERSON_HEIGHT / max(1, cutout.height)
    size = (max(1, round(cutout.width * scale)), TARGET_PERSON_HEIGHT)
    cutout = cutout.resize(size, Image.Resampling.LANCZOS)
    cutout_alpha = cutout_alpha.resize(size, Image.Resampling.LANCZOS)
    skin_crop = skin_crop.resize(size, Image.Resampling.LANCZOS)

    x = round(CENTER_X - size[0] / 2)
    y = GROUND_Y - size[1]
    body = BACKGROUND.copy()
    body.paste(cutout, (x, y), cutout_alpha)

    skin_layer = Image.new("L", CANVAS_SIZE, 0)
    skin_layer.paste(skin_crop, (x, y))
    skin_layer = skin_layer.filter(ImageFilter.GaussianBlur(1.0))
    return body, np.asarray(skin_layer, dtype=np.float32) / 255.0


def fallback_hair_mask(source, gender, style):
    rgb = np.asarray(source, dtype=np.float32)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    x, y = xx / w, yy / h
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = .299 * r + .587 * g + .114 * b

    if gender == "male":
        cx = .58
        bounds = {
            "male_textured": (.47, .70, .03, .32),
            "male_short": (.49, .68, .05, .29),
            "male_medium": (.45, .72, .02, .36),
            "male_undercut": (.47, .70, .03, .32),
            "male_slick": (.48, .69, .04, .31),
        }[style]
    else:
        cx = .52
        bounds = {
            "female_long": (.36, .68, .02, .72),
            "female_wavy": (.34, .70, .02, .74),
            "female_bob": (.38, .66, .02, .48),
            "female_ponytail": (.36, .70, .01, .64),
            "female_short": (.41, .63, .03, .36),
        }[style]

    x0, x1, y0, y1 = bounds
    region = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
    dark_or_hairlike = (lum < 145) & (r < 158) & (g < 145) & (b < 145)
    warm_dark = (r >= b * .78) | (lum < 62)
    layer = ((region & dark_or_hairlike & warm_dark).astype(np.uint8) * 255)
    layer = cv2.morphologyEx(layer, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    layer = cv2.morphologyEx(layer, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats((layer > 0).astype(np.uint8), 8)
    if n > 1:
        keep = np.zeros_like(layer)
        candidates = []
        for idx in range(1, n):
            sx, sy, sw, sh, area = stats[idx]
            if area < 60:
                continue
            ccx = (sx + sw / 2) / w
            ccy = (sy + sh / 2) / h
            score = area - 17000 * abs(ccx - cx) - 6500 * abs(ccy - .18)
            candidates.append((score, idx))
        # Long female hair can be split into left/right locks; retain up to 3
        # strongest nearby components instead of forcing one circular blob.
        for _, idx in sorted(candidates, reverse=True)[:3]:
            keep[labels == idx] = 255
        if keep.any():
            layer = keep
    return cv2.GaussianBlur(layer, (0, 0), 1.0).astype(np.float32) / 255.0


def align_style_hair(gender, style):
    source = fit_scene(STYLE_SOURCES[gender][style])
    try:
        hair_alpha, _ = base.masks(source, gender, style)
    except SystemExit:
        hair_alpha = fallback_hair_mask(source, gender, style)
    if np.count_nonzero(hair_alpha > .07) < 80:
        hair_alpha = fallback_hair_mask(source, gender, style)

    mask = np.clip(hair_alpha * 255, 0, 255).astype(np.uint8)
    ys, xs = np.where(mask > 12)
    if not len(xs):
        raise SystemExit(f"No usable hairstyle mask after fallback: {gender}/{style}")

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    rgb_crop = np.asarray(source, dtype=np.uint8)[y0:y1, x0:x1]
    a_crop = mask[y0:y1, x0:x1]

    max_w, max_h, top_y = HAIR_ENVELOPES[style]
    scale = min(max_w / max(1, rgb_crop.shape[1]), max_h / max(1, rgb_crop.shape[0]))
    out_w = max(1, round(rgb_crop.shape[1] * scale))
    out_h = max(1, round(rgb_crop.shape[0] * scale))
    rgb_crop = cv2.resize(rgb_crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    a_crop = cv2.resize(a_crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

    x = round(CENTER_X - out_w / 2)
    y = top_y
    aligned_rgb = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.float32)
    aligned_alpha = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0]), dtype=np.float32)
    x2 = min(CANVAS_SIZE[0], x + out_w)
    y2 = min(CANVAS_SIZE[1], y + out_h)
    if x < 0 or y < 0 or x2 <= x or y2 <= y:
        raise SystemExit(f"Invalid hairstyle placement: {gender}/{style}")

    cw, ch = x2 - x, y2 - y
    aligned_rgb[y:y2, x:x2] = rgb_crop[:ch, :cw].astype(np.float32)
    aligned_alpha[y:y2, x:x2] = a_crop[:ch, :cw].astype(np.float32) / 255.0
    aligned_alpha = cv2.GaussianBlur(aligned_alpha, (0, 0), 0.75)
    return aligned_rgb, np.clip(aligned_alpha, 0, 1)


def recolor_skin(rgb, alpha, target):
    src = rgb.astype(np.float32)
    a = np.clip(alpha, 0, 1)[..., None]
    target = np.asarray(target, dtype=np.float32)
    lum = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    selected = lum[alpha > .35]
    midpoint = float(np.median(selected)) if selected.size else 120.0
    detail = np.clip((lum - midpoint) / 255.0, -.11, .11)
    toned = np.clip(target[None, None, :] + detail[..., None] * 115.0, 0, 255)
    strength = .74
    return np.clip(src * (1 - a * strength) + toned * (a * strength), 0, 255)


def recolor_hair(rgb, alpha, target, name):
    src = rgb.astype(np.float32)
    target = np.asarray(target, dtype=np.float32)
    lum = .299 * src[..., 0] + .587 * src[..., 1] + .114 * src[..., 2]
    selected = lum[alpha > .25]
    low, high = (np.percentile(selected, (5, 97)) if selected.size else (18.0, 150.0))
    norm = np.clip((lum - low) / max(26.0, high - low), 0, 1)
    floors = {"black": .16, "brown": .27, "blond": .58, "red": .34, "purple": .28}
    ceilings = {"black": .64, "brown": .88, "blond": 1.18, "red": 1.02, "purple": .96}
    brightness = floors[name] + (ceilings[name] - floors[name]) * norm
    coloured = np.clip(target[None, None, :] * brightness[..., None], 0, 255)
    a = (np.clip(alpha, 0, 1) * .88)[..., None]
    return np.clip(src * (1 - a) + coloured * a, 0, 255)


def build():
    requested_gender = os.environ.get("CREATOR_BUILD_GENDER")
    written = 0

    for gender, styles in STYLE_SOURCES.items():
        if requested_gender and gender != requested_gender:
            continue

        body, skin_alpha = canonical_body(gender)
        body_rgb = np.asarray(body, dtype=np.float32)
        aligned_hair = {style: align_style_hair(gender, style) for style in styles}

        for skin_name, skin_rgb in base.SKINS.items():
            skinned = recolor_skin(body_rgb, skin_alpha, skin_rgb)

            for hair_name, hair_rgb in base.HAIRS.items():
                for style in styles:
                    hair_source, hair_alpha = aligned_hair[style]
                    hair_coloured = recolor_hair(hair_source, hair_alpha, hair_rgb, hair_name)
                    a = np.clip(hair_alpha, 0, 1)[..., None]
                    result = np.clip(skinned * (1 - a) + hair_coloured * a, 0, 255).astype(np.uint8)

                    out = Image.fromarray(result, "RGB")
                    path = base.OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    out.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
                    written += 1

    expected = 125 if requested_gender else 250
    if written != expected:
        raise SystemExit(f"Expected {expected} presets, wrote {written}")
    print(
        f"Built {written} canonical Rise Looter presets at {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]} "
        f"center={CENTER_X}, ground={GROUND_Y}, body_height={TARGET_PERSON_HEIGHT}"
    )


if __name__ == "__main__":
    build()
