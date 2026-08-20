from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_fullbody_hd as legacy


def canonical_person_mask(scene, gender):
    """Build one stable whole-person mask from the canonical scene.

    Unlike GrabCut, this uses the known empty background and then closes the
    detected silhouette with a convex hull. This deliberately prefers keeping
    the complete arms/legs over shaving pixels off the body edge.
    """
    rgb = np.asarray(scene, dtype=np.uint8)
    bg = np.asarray(legacy.BACKGROUND, dtype=np.uint8)
    delta = np.mean(np.abs(rgb.astype(np.int16) - bg.astype(np.int16)), axis=2)
    raw = (delta > 7.0).astype(np.uint8) * 255
    raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    raw = cv2.morphologyEx(raw, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    n, labels, stats, _ = cv2.connectedComponentsWithStats((raw > 0).astype(np.uint8), 8)
    if n <= 1:
        raise SystemExit(f"Could not isolate canonical {gender} body from background")

    h, w = raw.shape
    expected_cx = (.58 if gender == "male" else .52) * w
    best = None
    for idx in range(1, n):
        x, y, cw, ch, area = stats[idx]
        if area < h * w * .008 or ch < h * .30:
            continue
        cx = x + cw / 2
        score = area + ch * 180 - abs(cx - expected_cx) * 110
        if best is None or score > best[0]:
            best = (score, idx, x, y, cw, ch)
    if best is None:
        raise SystemExit(f"No full-height canonical {gender} component")

    _, primary, x, y, cw, ch = best
    pad_x = max(18, int(cw * .28))
    pad_y = max(8, int(ch * .035))
    x0, x1 = max(0, x - pad_x), min(w, x + cw + pad_x)
    y0, y1 = max(0, y - pad_y), min(h, y + ch + pad_y)

    # Keep every meaningful difference component around the canonical body so a
    # separated forearm/hand cannot disappear just because it was disconnected.
    support = np.zeros_like(raw)
    for idx in range(1, n):
        sx, sy, sw, sh, area = stats[idx]
        if area < 45:
            continue
        ccx, ccy = sx + sw / 2, sy + sh / 2
        if x0 <= ccx <= x1 and y0 <= ccy <= y1:
            support[labels == idx] = 255
    support[labels == primary] = 255

    ys, xs = np.where(support > 0)
    if not len(xs):
        raise SystemExit(f"Empty canonical {gender} support")

    hull = cv2.convexHull(np.column_stack([xs, ys]).astype(np.int32))
    keep = np.zeros_like(raw)
    cv2.fillConvexPoly(keep, hull, 255)
    keep = cv2.dilate(keep, np.ones((3, 3), np.uint8), iterations=1)
    keep = cv2.GaussianBlur(keep, (0, 0), .8)

    ys, xs = np.where(keep > 20)
    bbox_h = ys.max() - ys.min() + 1
    if bbox_h < h * .48:
        raise SystemExit(f"Canonical {gender} body is not full-height enough ({bbox_h}/{h})")
    return Image.fromarray(keep, "L")


def anatomical_skin_mask(scene, person_alpha):
    """Tint only genuine exposed skin around face/neck, never clothing.

    The previous colour threshold was allowed over the entire body, so warm
    hoodie/fabric pixels were incorrectly classified as skin. This mask first
    restricts the operation to anatomical face/neck regions and only then uses
    colour classification.
    """
    rgb = np.asarray(scene, dtype=np.uint8)
    alpha = np.asarray(person_alpha, dtype=np.uint8)
    ys, xs = np.where(alpha > 40)
    if not len(xs):
        raise SystemExit("Cannot build skin mask without canonical person")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    bw, bh = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    cx = (x0 + x1) / 2.0

    yy, xx = np.mgrid[0:rgb.shape[0], 0:rgb.shape[1]]
    face_cy = y0 + bh * .115
    neck_cy = y0 + bh * .205
    face = (((xx - cx) / max(22.0, bw * .145)) ** 2 + ((yy - face_cy) / max(30.0, bh * .105)) ** 2) <= 1.0
    neck = (((xx - cx) / max(18.0, bw * .105)) ** 2 + ((yy - neck_cy) / max(14.0, bh * .040)) ** 2) <= 1.0
    anatomical = face | neck

    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    lum, cr, cb = cv2.split(ycrcb)
    skinlike = (cr >= 127) & (cr <= 178) & (cb >= 76) & (cb <= 136) & (lum >= 38)
    layer = (skinlike & anatomical & (alpha > 70)).astype(np.uint8) * 255
    layer = cv2.morphologyEx(layer, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    layer = cv2.morphologyEx(layer, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    layer = cv2.GaussianBlur(layer, (0, 0), 1.0)
    return Image.fromarray(layer, "L")


def fixed_canonical_body(gender):
    path, _ = legacy.CANONICAL[gender]
    scene = legacy.fit_scene(path)
    person_alpha = canonical_person_mask(scene, gender)
    bbox = person_alpha.getbbox()
    if not bbox:
        raise SystemExit(f"No canonical {gender} body bbox")

    skin = anatomical_skin_mask(scene, person_alpha)
    cutout = scene.crop(bbox)
    cutout_alpha = person_alpha.crop(bbox)
    skin_crop = skin.crop(bbox)

    target_h = legacy.TARGET_PERSON_HEIGHT
    scale = target_h / max(1, cutout.height)
    target_w = max(1, round(cutout.width * scale))
    cutout = cutout.resize((target_w, target_h), Image.Resampling.LANCZOS)
    cutout = cutout.filter(ImageFilter.UnsharpMask(radius=.75, percent=80, threshold=4))
    cutout_alpha = cutout_alpha.resize((target_w, target_h), Image.Resampling.LANCZOS)
    skin_crop = skin_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)

    x = round(legacy.CENTER_X - target_w / 2)
    y = legacy.GROUND_Y - target_h
    if x < 0 or x + target_w > legacy.CANVAS_SIZE[0] or y < 0:
        raise SystemExit(f"Canonical {gender} placement clips canvas")

    # This body is built once per gender and is reused byte-for-byte as the base
    # for every skin/hair/style combination in legacy.build().
    body = legacy.BACKGROUND.copy()
    body.paste(cutout, (x, y), cutout_alpha)

    skin_layer = Image.new("L", legacy.CANVAS_SIZE, 0)
    skin_layer.paste(skin_crop, (x, y))
    skin_layer = skin_layer.filter(ImageFilter.GaussianBlur(.7))
    return body, np.asarray(skin_layer, dtype=np.float32) / 255.0


def hair_shape_envelope(gender, style, h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    xn = xx / float(w)
    yn = yy / float(h)
    if gender == "male":
        cx = .58
        rx, ry = {
            "male_textured": (.105, .115),
            "male_short": (.090, .100),
            "male_medium": (.120, .145),
            "male_undercut": (.105, .115),
            "male_slick": (.105, .110),
        }[style]
        cy = .155
        env = 1.0 - np.clip(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2, 0, 1)
        face = (((xn-cx)/.062)**2 + ((yn-.235)/.082)**2) < 1.0
        env[face] = 0
    else:
        cx = .52
        top = 1.0 - np.clip(((xn-cx)/.13)**2 + ((yn-.16)/.15)**2, 0, 1)
        side_l = 1.0 - np.clip(((xn-(cx-.085))/.075)**2 + ((yn-.34)/.30)**2, 0, 1)
        side_r = 1.0 - np.clip(((xn-(cx+.085))/.075)**2 + ((yn-.34)/.30)**2, 0, 1)
        if style in ("female_bob", "female_short"):
            side_l *= (yn < .46)
            side_r *= (yn < .46)
        env = np.maximum(top, np.maximum(side_l, side_r))
        face = (((xn-cx)/.058)**2 + ((yn-.235)/.080)**2) < 1.0
        env[face] = 0
    return cv2.GaussianBlur(np.clip(env, 0, 1).astype(np.float32), (0, 0), 1.2)


def safe_align_style_hair(gender, style):
    source = legacy.fit_scene(legacy.STYLE_SOURCES[gender][style])
    raw = legacy.fallback_hair_mask(source, gender, style)
    h, w = raw.shape
    hair_alpha = np.clip(raw * hair_shape_envelope(gender, style, h, w), 0, 1)
    mask = np.clip(hair_alpha * 255, 0, 255).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0, 0), .75)
    ys, xs = np.where(mask > 12)
    if not len(xs):
        raise SystemExit(f"No safe hairstyle mask: {gender}/{style}")

    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    rgb_crop = np.asarray(source, dtype=np.uint8)[y0:y1, x0:x1]
    a_crop = mask[y0:y1, x0:x1]
    fill_ratio = float(np.count_nonzero(a_crop > 96)) / max(1, a_crop.size)
    edge_ratio = max(np.mean(a_crop[0] > 96), np.mean(a_crop[-1] > 96), np.mean(a_crop[:, 0] > 96), np.mean(a_crop[:, -1] > 96))
    if fill_ratio > .72 or edge_ratio > .55:
        raise SystemExit(f"Unsafe rectangular hairstyle mask rejected: {gender}/{style} fill={fill_ratio:.3f} edge={edge_ratio:.3f}")

    max_w, max_h, top_y = legacy.HAIR_ENVELOPES[style]
    scale = min(max_w / max(1, rgb_crop.shape[1]), max_h / max(1, rgb_crop.shape[0]))
    out_w = max(1, round(rgb_crop.shape[1] * scale))
    out_h = max(1, round(rgb_crop.shape[0] * scale))
    rgb_crop = cv2.resize(rgb_crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    a_crop = cv2.resize(a_crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)

    x = round(legacy.CENTER_X - out_w / 2)
    y = top_y
    aligned_rgb = np.zeros((legacy.CANVAS_SIZE[1], legacy.CANVAS_SIZE[0], 3), dtype=np.float32)
    aligned_alpha = np.zeros((legacy.CANVAS_SIZE[1], legacy.CANVAS_SIZE[0]), dtype=np.float32)
    x2 = min(legacy.CANVAS_SIZE[0], x + out_w)
    y2 = min(legacy.CANVAS_SIZE[1], y + out_h)
    if x < 0 or y < 0 or x2 <= x or y2 <= y:
        raise SystemExit(f"Invalid hairstyle placement: {gender}/{style}")
    cw, ch = x2 - x, y2 - y
    aligned_rgb[y:y2, x:x2] = rgb_crop[:ch, :cw].astype(np.float32)
    aligned_alpha[y:y2, x:x2] = a_crop[:ch, :cw].astype(np.float32) / 255.0
    # Hair is never allowed to affect the torso, arms, legs or clothes.
    aligned_alpha[int(legacy.CANVAS_SIZE[1] * .36):, :] = 0.0
    aligned_alpha = cv2.GaussianBlur(aligned_alpha, (0, 0), .72)
    aligned_alpha[int(legacy.CANVAS_SIZE[1] * .38):, :] = 0.0
    return aligned_rgb, np.clip(aligned_alpha, 0, 1)


legacy.canonical_body = fixed_canonical_body
legacy.align_style_hair = safe_align_style_hair
legacy.build()
