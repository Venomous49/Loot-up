from pathlib import Path
import os
import sys

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_from_hairstyle_masters as base

CANVAS_SIZE = (1728, 910)
TARGET_PERSON_HEIGHT = 820
MAX_PERSON_WIDTH = 900
GROUND_Y = 900
CENTER_X = 1110
WEBP_QUALITY = 98


def master_background():
    bg = Image.open(base.BACKGROUND).convert("RGB")
    if bg.size != CANVAS_SIZE:
        bg = ImageOps.fit(bg, CANVAS_SIZE, Image.Resampling.LANCZOS)
    return bg


BACKGROUND = master_background()


def reviewed_alpha(style, override_mask=None):
    mask_path = override_mask or (base.MASKS / f"{style}.png")
    if not mask_path.exists():
        raise SystemExit(f"Missing reviewed person mask: {mask_path}")
    alpha = Image.open(mask_path).convert("L")
    if alpha.size != CANVAS_SIZE:
        alpha = ImageOps.fit(alpha, CANVAS_SIZE, Image.Resampling.LANCZOS)
    return alpha


def composite_full_body(scene, style, override_mask=None):
    """Place every avatar on the exact same 1728x910 set and ground line.

    The person is scaled uniformly from the reviewed silhouette, never stretched,
    so body/face proportions remain photographic. Male and female assets share
    the same canvas, center axis, ground line and target standing height.

    Hair can legitimately make the silhouette wider (especially female long and
    wavy styles), so height is the primary normalization constraint. A generous
    width guard only prevents accidental clipping; it must never shrink a normal
    full-body avatar into a torso-sized render.
    """
    portrait = scene.convert("RGB")
    if portrait.size != CANVAS_SIZE:
        portrait = ImageOps.fit(portrait, CANVAS_SIZE, Image.Resampling.LANCZOS)

    alpha = reviewed_alpha(style, override_mask)
    bbox = alpha.getbbox()
    if not bbox:
        raise SystemExit(f"Empty creator silhouette: {style}")

    person = portrait.crop(bbox)
    person_alpha = alpha.crop(bbox)
    source_w, source_h = person.size
    if source_h <= 0 or source_w <= 0:
        raise SystemExit(f"Invalid creator silhouette bounds: {style}")

    height_scale = TARGET_PERSON_HEIGHT / source_h
    width_guard_scale = MAX_PERSON_WIDTH / source_w
    scale = min(height_scale, width_guard_scale)

    target_w = max(1, round(source_w * scale))
    target_h = max(1, round(source_h * scale))

    person = person.resize((target_w, target_h), Image.Resampling.LANCZOS)
    person_alpha = person_alpha.resize((target_w, target_h), Image.Resampling.LANCZOS)

    x = round(CENTER_X - target_w / 2)
    y = GROUND_Y - target_h
    if x < 0 or x + target_w > CANVAS_SIZE[0] or y < 0 or y + target_h > CANVAS_SIZE[1]:
        raise SystemExit(f"Creator placement clips canvas for {style}: {(x, y, target_w, target_h)}")

    canvas = BACKGROUND.copy()
    canvas.paste(person, (x, y), person_alpha)
    return canvas


def build():
    written = 0
    requested_gender = os.environ.get("CREATOR_BUILD_GENDER")

    for gender, styles in base.MASTERS.items():
        if requested_gender and gender != requested_gender:
            continue

        for style, source in styles.items():
            if not source.exists():
                raise SystemExit(f"Missing hairstyle master: {source}")

            master = Image.open(source).convert("RGB")
            if master.size != CANVAS_SIZE:
                master = ImageOps.fit(master, CANVAS_SIZE, Image.Resampling.LANCZOS)
            source_rgb = np.asarray(master).astype(np.float32)
            hair_mask, skin_mask = base.masks(master, gender, style)
            if hair_mask.sum() < 250:
                raise SystemExit(f"Unsafe hair mask for {gender}/{style}")

            color_bases = {}
            for (override_style, hair_name), override_source in base.COLOR_MASTERS.items():
                if override_style != style:
                    continue
                override = Image.open(override_source).convert("RGB")
                if override.size != CANVAS_SIZE:
                    override = ImageOps.fit(override, CANVAS_SIZE, Image.Resampling.LANCZOS)
                override_base = np.asarray(override).astype(np.float32)
                override_skin_mask = base.standardized_override_skin_mask(override, gender)
                override_mask = base.COLOR_MASKS / override_source.with_suffix(".png").name
                if not override_mask.exists():
                    raise SystemExit(f"Missing colour-master person mask: {override_mask}")
                color_bases[hair_name] = (override_base, override_skin_mask, override_mask)

            for skin_name, skin_rgb in base.SKINS.items():
                skin_strength = .50 if gender == "female" else .60
                skinned = base.tint_skin(source_rgb, skin_mask, skin_rgb, strength=skin_strength)

                for hair_name, hair_rgb in base.HAIRS.items():
                    is_color_master = hair_name in color_bases
                    override_mask = None

                    if is_color_master:
                        override_base, override_skin_mask, override_mask = color_bases[hair_name]
                        result = base.tint_skin(
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
                        result = base.tint(
                            skinned,
                            hair_mask,
                            hair_rgb,
                            hair_strength,
                            hair_floor,
                            True,
                            hair_ceiling,
                        ).astype(np.uint8)

                    scene = Image.fromarray(result, "RGB")
                    output = composite_full_body(scene, style, override_mask)
                    path = base.OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    # Near-lossless WebP keeps skin texture and hair detail while
                    # retaining the exact approved street background composition.
                    output.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
                    written += 1

    expected = 125 if requested_gender else 250
    if written != expected:
        raise SystemExit(f"Expected {expected} presets, wrote {written}")
    print(
        f"Built {written} Rise Looter presets at {CANVAS_SIZE[0]}x{CANVAS_SIZE[1]} "
        f"with shared center x={CENTER_X}, ground y={GROUND_Y}, standing height={TARGET_PERSON_HEIGHT}px"
    )


if __name__ == "__main__":
    build()
