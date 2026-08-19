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

# One immutable body/pose/outfit/face reference per gender. Every preset is
# rebuilt from these two bodies; only complexion, hairstyle and hair colour may
# change. The male reference is the approved full-body undercut artwork.
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


def canonical_body(gender):
    path, style = CANONICAL[gender]
    scene = fit_scene(path)
    alpha = reviewed_mask(style)
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit(f"Empty canonical mask: {gender}")

    cutout = scene.crop(bbox)
    cutout_alpha = alpha.crop(bbox)
    scale = TARGET_PERSON_HEIGHT / max(1, cutout.height)
    size = (max(1, round(cutout.width * scale)), TARGET_PERSON_HEIGHT)
    cutout = cutout.resize(size, Image.Resampling.LANCZOS)
    cutout_alpha = cutout_alpha.resize(size, Image.Resampling.LANCZOS)

    x = round(CENTER_X - size[0] / 2)
    y = GROUND_Y - size[1]
    body = BACKGROUND.copy()
    body.paste(cutout, (x, y), cutout_alpha)

    # Carry one continuous skin mask through the exact body crop/scale/position.
    # That removes the neck/face boundary that occurred when each hairstyle was
    # independently recoloured.
    _, source_skin = base.masks(scene, gender, style)
    source_skin = Image.fromarray(np.clip(source_skin * 255, 0, 255).astype(np.uint8), "L")
    source_skin = source_skin.crop(bbox).resize(size, Image.Resampling.LANCZOS)
    skin_layer = Image.new("L", CANVAS_SIZE, 0)
    skin_layer.paste(source_skin, (x, y))
    skin_layer = skin_layer.filter(ImageFilter.GaussianBlur(1.2))

    return body, np.asarray(skin_layer, dtype=np.float32) / 255.0


def align_style_hair(gender, style, canonical):
    source = fit_scene(STYLE_SOURCES[gender][style])
    hair_alpha, _ = base.masks(source, gender, style)

    sx, sy, sw, sh = base.detect_face(source)
    tx, ty, tw, th = base.detect_face(canonical)
    scale = th / max(1.0, sh)
    src_center = np.array([sx + sw / 2.0, sy + sh / 2.0], dtype=np.float32)
    dst_center = np.array([tx + tw / 2.0, ty + th / 2.0], dtype=np.float32)
    matrix = np.array([
        [scale, 0.0, dst_center[0] - src_center[0] * scale],
        [0.0, scale, dst_center[1] - src_center[1] * scale],
    ], dtype=np.float32)

    rgb = np.asarray(source, dtype=np.uint8)
    aligned_rgb = cv2.warpAffine(
        rgb, matrix, CANVAS_SIZE, flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0)
    )
    aligned_alpha = cv2.warpAffine(
        np.clip(hair_alpha * 255, 0, 255).astype(np.uint8), matrix, CANVAS_SIZE,
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0
    ).astype(np.float32) / 255.0

    # Feather only the true hairstyle silhouette; never draw synthetic circles.
    aligned_alpha = cv2.GaussianBlur(aligned_alpha, (0, 0), 0.8)
    return aligned_rgb.astype(np.float32), np.clip(aligned_alpha, 0, 1)


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
        aligned_hair = {style: align_style_hair(gender, style, body) for style in styles}

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
