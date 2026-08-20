from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_fullbody_hd as legacy


def immutable_canonical_body(gender):
    """Use the reviewed canonical scene itself as the immutable full-body base.

    No person segmentation, GrabCut, convex hull, crop, resize or repaste is
    allowed here. This is deliberate: arms, legs, clothes, pose and silhouette
    must remain byte-for-byte geometrically identical for every preset.
    """
    path, _ = legacy.CANONICAL[gender]
    scene = legacy.fit_scene(path)
    rgb = np.asarray(scene, dtype=np.uint8)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]

    cx = legacy.CENTER_X
    # Only exposed face/neck may receive complexion changes. Clothing and body
    # silhouette are never part of this mask.
    face = (((xx - cx) / 72.0) ** 2 + ((yy - 220.0) / 88.0) ** 2) <= 1.0
    neck = (((xx - cx) / 48.0) ** 2 + ((yy - 292.0) / 42.0) ** 2) <= 1.0
    anatomical = face | neck

    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    lum, cr, cb = cv2.split(ycrcb)
    skinlike = (cr >= 126) & (cr <= 184) & (cb >= 72) & (cb <= 142) & (lum >= 28)
    mask = (skinlike & anatomical).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0, 0), .65)
    return scene, mask.astype(np.float32) / 255.0


def _tight_hair_envelope(gender, style, h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    xn = xx / float(w)
    yn = yy / float(h)
    if gender == "male":
        cx = .58
        rx, ry, cy = {
            "male_textured": (.082, .090, .160),
            "male_short": (.074, .078, .165),
            "male_medium": (.094, .112, .158),
            "male_undercut": (.082, .090, .160),
            "male_slick": (.082, .084, .160),
        }[style]
        env = 1.0 - np.clip(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2, 0, 1)
        # Never let a hairstyle layer paint over the face.
        face = (((xn-cx)/.052)**2 + ((yn-.235)/.067)**2) <= 1.0
        env[face] = 0.0
    else:
        cx = .52
        top = 1.0 - np.clip(((xn-cx)/.115)**2 + ((yn-.165)/.125)**2, 0, 1)
        side_l = 1.0 - np.clip(((xn-(cx-.075))/.060)**2 + ((yn-.33)/.25)**2, 0, 1)
        side_r = 1.0 - np.clip(((xn-(cx+.075))/.060)**2 + ((yn-.33)/.25)**2, 0, 1)
        if style in ("female_bob", "female_short"):
            side_l *= (yn < .43)
            side_r *= (yn < .43)
        env = np.maximum(top, np.maximum(side_l, side_r))
        face = (((xn-cx)/.052)**2 + ((yn-.235)/.070)**2) <= 1.0
        env[face] = 0.0
    return np.clip(env, 0, 1).astype(np.float32)


def scalp_only_hair(gender, style):
    """Extract only opaque hairstyle pixels; never source background/halo."""
    source = legacy.fit_scene(legacy.STYLE_SOURCES[gender][style])
    raw = legacy.fallback_hair_mask(source, gender, style)
    h, w = raw.shape
    shaped = np.clip(raw * _tight_hair_envelope(gender, style, h, w), 0, 1)

    # Weak semi-transparent source pixels are what produced the smoke/halo.
    # Convert to a reviewed-looking solid hair silhouette before feathering only
    # the final 1px-ish edge.
    mask = (shaped >= .24).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        raise SystemExit(f"No clean hairstyle component: {gender}/{style}")
    candidates = []
    for idx in range(1, n):
        x, y, cw, ch, area = stats[idx]
        if area < 45:
            continue
        candidates.append((area, idx))
    if not candidates:
        raise SystemExit(f"No clean hairstyle pixels: {gender}/{style}")
    keep = np.zeros_like(mask)
    for _, idx in sorted(candidates, reverse=True)[:2]:
        keep[labels == idx] = 255
    mask = cv2.GaussianBlur(keep, (0, 0), .38)

    ys, xs = np.where(mask > 24)
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

    x = round(legacy.CENTER_X - out_w / 2)
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

    # Absolute safety boundary: hairstyle can never touch torso/arms/clothes.
    alpha_out[int(legacy.CANVAS_SIZE[1] * .34):, :] = 0.0
    return rgb_out, np.clip(alpha_out, 0, 1)


legacy.canonical_body = immutable_canonical_body
legacy.align_style_hair = scalp_only_hair
legacy.build()
