from pathlib import Path
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_fullbody_hd as legacy


def base_center_x(gender, width):
    # Canonical source scenes are intentionally not moved.  Male stands around
    # 58% of the scene width, female around 52%; overlays must follow the base.
    return int(round(width * (.58 if gender == "male" else .52)))


def immutable_canonical_body(gender):
    """Return the reviewed full scene unchanged as the immutable creator base.

    No segmentation/crop/resize/repaste is allowed: arms, legs, clothes, pose,
    silhouette and background remain exactly where they are in the source.
    """
    path, _ = legacy.CANONICAL[gender]
    scene = legacy.fit_scene(path)
    rgb = np.asarray(scene, dtype=np.uint8)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx = base_center_x(gender, w)

    # Complexion is restricted to face + neck only.  No arm or clothing pixels
    # can ever enter this mask.
    face_cy = int(round(h * .235))
    neck_cy = int(round(h * .315))
    face = (((xx - cx) / 70.0) ** 2 + ((yy - face_cy) / 86.0) ** 2) <= 1.0
    neck = (((xx - cx) / 46.0) ** 2 + ((yy - neck_cy) / 40.0) ** 2) <= 1.0
    anatomical = face | neck

    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    lum, cr, cb = cv2.split(ycrcb)
    skinlike = (cr >= 126) & (cr <= 184) & (cb >= 72) & (cb <= 142) & (lum >= 28)
    mask = (skinlike & anatomical).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0, 0), .55)
    return scene, mask.astype(np.float32) / 255.0


def _tight_hair_envelope(gender, style, h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    xn = xx / float(w)
    yn = yy / float(h)
    if gender == "male":
        cx = .58
        rx, ry, cy = {
            "male_textured": (.075, .078, .160),
            "male_short": (.068, .070, .165),
            "male_medium": (.086, .100, .158),
            "male_undercut": (.075, .078, .160),
            "male_slick": (.076, .074, .160),
        }[style]
        env = 1.0 - np.clip(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2, 0, 1)
        face = (((xn-cx)/.050)**2 + ((yn-.235)/.065)**2) <= 1.0
        env[face] = 0.0
    else:
        cx = .52
        top = 1.0 - np.clip(((xn-cx)/.110)**2 + ((yn-.165)/.120)**2, 0, 1)
        side_l = 1.0 - np.clip(((xn-(cx-.072))/.058)**2 + ((yn-.33)/.24)**2, 0, 1)
        side_r = 1.0 - np.clip(((xn-(cx+.072))/.058)**2 + ((yn-.33)/.24)**2, 0, 1)
        if style in ("female_bob", "female_short"):
            side_l *= (yn < .43)
            side_r *= (yn < .43)
        env = np.maximum(top, np.maximum(side_l, side_r))
        face = (((xn-cx)/.050)**2 + ((yn-.235)/.068)**2) <= 1.0
        env[face] = 0.0
    return np.clip(env, 0, 1).astype(np.float32)


def scalp_only_hair(gender, style):
    """Extract opaque hairstyle pixels only, with no rectangular source halo."""
    source = legacy.fit_scene(legacy.STYLE_SOURCES[gender][style])
    raw = legacy.fallback_hair_mask(source, gender, style)
    h, w = raw.shape
    shaped = np.clip(raw * _tight_hair_envelope(gender, style, h, w), 0, 1)

    # Kill smoke/halo pixels before the final tiny edge feather.
    mask = (shaped >= .34).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        raise SystemExit(f"No clean hairstyle component: {gender}/{style}")
    candidates = []
    for idx in range(1, n):
        x, y, cw, ch, area = stats[idx]
        if area >= 45:
            candidates.append((area, idx))
    if not candidates:
        raise SystemExit(f"No clean hairstyle pixels: {gender}/{style}")
    keep = np.zeros_like(mask)
    for _, idx in sorted(candidates, reverse=True)[:2]:
        keep[labels == idx] = 255
    mask = cv2.GaussianBlur(keep, (0, 0), .28)

    ys, xs = np.where(mask > 40)
    if not len(xs):
        raise SystemExit(f"Empty clean hairstyle: {gender}/{style}")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    rgb_crop = np.asarray(source, dtype=np.uint8)[y0:y1, x0:x1]
    a_crop = mask[y0:y1, x0:x1]

    max_w, max_h, top_y = legacy.HAIR_ENVELOPES[style]
    scale = min(max_w / max(1, rgb_crop.shape[1]), max_h / max(1, rgb_crop.shape[0]))
    out_w = max(1, round(rgb_crop.shape[1] * scale))
    out_h = max(1, round(rgb_crop.shape[0] * scale))
    rgb_crop = cv2.resize(rgb_crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    a_crop = cv2.resize(a_crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

    cx = base_center_x(gender, legacy.CANVAS_SIZE[0])
    x = round(cx - out_w / 2)
    y = top_y
    rgb_out = np.zeros((legacy.CANVAS_SIZE[1], legacy.CANVAS_SIZE[0], 3), dtype=np.float32)
    alpha_out = np.zeros((legacy.CANVAS_SIZE[1], legacy.CANVAS_SIZE[0]), dtype=np.float32)
    x2 = min(legacy.CANVAS_SIZE[0], x + out_w)
    y2 = min(legacy.CANVAS_SIZE[1], y + out_h)
    cw, ch = x2 - x, y2 - y
    if x < 0 or y < 0 or cw <= 0 or ch <= 0:
        raise SystemExit(f"Invalid clean hairstyle placement: {gender}/{style}")
    rgb_out[y:y2, x:x2] = rgb_crop[:ch, :cw].astype(np.float32)
    alpha_out[y:y2, x:x2] = a_crop[:ch, :cw].astype(np.float32) / 255.0

    # Absolute safety boundary: hair never touches torso, arms or clothes.
    alpha_out[int(legacy.CANVAS_SIZE[1] * .34):, :] = 0.0
    alpha_out[alpha_out < .12] = 0.0
    return rgb_out, np.clip(alpha_out, 0, 1)


legacy.canonical_body = immutable_canonical_body
legacy.align_style_hair = scalp_only_hair
legacy.build()
