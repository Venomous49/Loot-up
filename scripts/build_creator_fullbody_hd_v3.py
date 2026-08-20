from pathlib import Path
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_creator_fullbody_hd as legacy


def native_scene(path):
    if not path.exists():
        raise SystemExit(f"Missing creator source: {path}")
    return Image.open(path).convert("RGB")


def robust_person_mask(image, gender):
    rgb = np.asarray(image, dtype=np.uint8)
    h, w = rgb.shape[:2]
    preview_w = min(700, w)
    scale = preview_w / w
    preview = cv2.resize(rgb, (preview_w, max(2, round(h * scale))), interpolation=cv2.INTER_AREA)
    ph, pw = preview.shape[:2]
    gc = np.zeros((ph, pw), np.uint8)
    rect = (int((.24 if gender == "male" else .20) * pw), int(.01 * ph), int((.52 if gender == "male" else .60) * pw), int(.98 * ph))
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(preview, gc, rect, bgd, fgd, 7, cv2.GC_INIT_WITH_RECT)
    mask = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats((mask > 0).astype(np.uint8), 8)
    if n <= 1:
        raise SystemExit(f"Could not isolate canonical {gender} body")
    center_x = pw / 2
    best = None
    for idx in range(1, n):
        x, y, cw, ch, area = stats[idx]
        if area < ph * pw * .015:
            continue
        score = area - abs((x + cw / 2) - center_x) * 180
        if best is None or score > best[0]:
            best = (score, idx)
    if best is None:
        raise SystemExit(f"No safe canonical {gender} component")
    keep = np.where(labels == best[1], 255, 0).astype(np.uint8)
    keep = cv2.resize(keep, (w, h), interpolation=cv2.INTER_LINEAR)
    keep = cv2.GaussianBlur(keep, (0, 0), 1.1)
    ys, xs = np.where(keep > 20)
    if not len(xs) or ys.max() - ys.min() + 1 < h * .48:
        raise SystemExit(f"Canonical {gender} extraction is not full-body enough")
    return Image.fromarray(keep, "L")


def native_skin_mask(scene, person_alpha):
    rgb = np.asarray(scene, dtype=np.uint8)
    alpha = np.asarray(person_alpha, dtype=np.uint8)
    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    yy, cr, cb = cv2.split(ycrcb)
    skin = (cr >= 128) & (cr <= 180) & (cb >= 76) & (cb <= 138) & (yy >= 34) & (alpha > 70)
    layer = skin.astype(np.uint8) * 255
    layer = cv2.morphologyEx(layer, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    layer = cv2.morphologyEx(layer, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return Image.fromarray(cv2.GaussianBlur(layer, (0, 0), 1.15), "L")


def neutralize_male_base_hair(scene):
    """Erase the canonical male haircut before applying selectable hairstyles.

    Previous versions only targeted dark pixels, so a left-side tuft survived and
    visually looked like a persistent horizontal offset. This version removes the
    full scalp/hair silhouette while explicitly protecting the face.
    """
    rgb = np.asarray(scene, dtype=np.uint8).copy()
    fx, fy, fw, fh = legacy.base.detect_face(scene)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]

    cx = fx + fw * .50
    scalp = (((xx - cx) / (fw * 1.03)) ** 2 + ((yy - (fy + fh * .02)) / (fh * .82)) ** 2) <= 1.0
    side_left = (((xx - (fx + fw * .05)) / (fw * .38)) ** 2 + ((yy - (fy + fh * .23)) / (fh * .48)) ** 2) <= 1.0
    side_right = (((xx - (fx + fw * .95)) / (fw * .34)) ** 2 + ((yy - (fy + fh * .23)) / (fh * .46)) ** 2) <= 1.0

    face_protect = (((xx - cx) / (fw * .50)) ** 2 + ((yy - (fy + fh * .60)) / (fh * .58)) ** 2) <= 1.0
    top_limit = yy < (fy + fh * .43)
    erase = (scalp | side_left | side_right) & top_limit & ~face_protect

    mask = erase.astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=1)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.4)
    _, mask = cv2.threshold(mask, 24, 255, cv2.THRESH_BINARY)

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cleaned = cv2.inpaint(bgr, mask, 7, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(cleaned, cv2.COLOR_BGR2RGB), "RGB")


def robust_canonical_body(gender):
    path, _ = legacy.CANONICAL[gender]
    original_scene = native_scene(path)
    scene = neutralize_male_base_hair(original_scene) if gender == "male" else original_scene
    person_alpha = robust_person_mask(original_scene, gender)
    bbox = person_alpha.getbbox()
    if not bbox:
        raise SystemExit(f"No canonical {gender} body bbox")
    skin = native_skin_mask(original_scene, person_alpha)
    cutout = scene.crop(bbox)
    cutout_alpha = person_alpha.crop(bbox)
    skin_crop = skin.crop(bbox)
    target_h = legacy.TARGET_PERSON_HEIGHT
    scale = target_h / max(1, cutout.height)
    target_w = max(1, round(cutout.width * scale))
    cutout = cutout.resize((target_w, target_h), Image.Resampling.LANCZOS)
    cutout = cutout.filter(ImageFilter.UnsharpMask(radius=.75, percent=85, threshold=4))
    cutout_alpha = cutout_alpha.resize((target_w, target_h), Image.Resampling.LANCZOS)
    skin_crop = skin_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = round(legacy.CENTER_X - target_w / 2)
    y = legacy.GROUND_Y - target_h
    body = legacy.BACKGROUND.copy()
    body.paste(cutout, (x, y), cutout_alpha)
    skin_layer = Image.new("L", legacy.CANVAS_SIZE, 0)
    skin_layer.paste(skin_crop, (x, y))
    skin_layer = skin_layer.filter(ImageFilter.GaussianBlur(.8))
    fx, fy, fw, fh = legacy.base.detect_face(original_scene)
    left, top, _, _ = bbox
    face_center_x = x + ((fx + fw * .50) - left) * scale
    face_top_y = y + (fy - top) * scale
    head_anchor = (float(face_center_x), float(face_top_y), float(fw * scale), float(fh * scale))
    return body, np.asarray(skin_layer, dtype=np.float32) / 255.0, head_anchor


def hair_shape_envelope(gender, style, h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    xn = xx / float(w)
    yn = yy / float(h)
    if gender == "male":
        cx = .58
        rx, ry = {"male_textured": (.105, .115), "male_short": (.090, .100), "male_medium": (.120, .145), "male_undercut": (.105, .115), "male_slick": (.105, .110)}[style]
        cy = .155
        env = 1.0 - np.clip(((xn-cx)/rx)**2 + ((yn-cy)/ry)**2, 0, 1)
        face = (((xn-cx)/.062)**2 + ((yn-.235)/.082)**2) < 1.0
        env[face] = 0
        env[yn > .295] = 0
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


def safe_align_style_hair(gender, style, head_anchor=None):
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
    if gender == "male":
        scale *= 1.07
    out_w = max(1, round(rgb_crop.shape[1] * scale))
    out_h = max(1, round(rgb_crop.shape[0] * scale))
    rgb_crop = cv2.resize(rgb_crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    a_crop = cv2.resize(a_crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)
    if gender == "male" and head_anchor is not None:
        face_center_x, _, _, _ = head_anchor
        # Deployed screenshot still shows the selectable hairstyle to the right.
        # Shift all five male styles 6px further left: total = -18px.
        x = round(face_center_x - out_w / 2) - 18
        y = top_y + 11
    else:
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
    aligned_alpha = cv2.GaussianBlur(aligned_alpha, (0, 0), 0.72)
    if gender == "male":
        aligned_alpha[330:, :] = 0
    return aligned_rgb, np.clip(aligned_alpha, 0, 1)


def build_locked_presets():
    requested_gender = os.environ.get("CREATOR_BUILD_GENDER")
    written = 0
    for gender, styles in legacy.STYLE_SOURCES.items():
        if requested_gender and gender != requested_gender:
            continue
        fixed_body, skin_alpha, head_anchor = robust_canonical_body(gender)
        fixed_rgb = np.asarray(fixed_body, dtype=np.float32)
        aligned_hair = {style: safe_align_style_hair(gender, style, head_anchor) for style in styles}
        for skin_name, skin_rgb in legacy.base.SKINS.items():
            skinned = legacy.recolor_skin(fixed_rgb, skin_alpha, skin_rgb)
            for hair_name, hair_rgb in legacy.base.HAIRS.items():
                for style in styles:
                    hair_source, hair_alpha = aligned_hair[style]
                    hair_coloured = legacy.recolor_hair(hair_source, hair_alpha, hair_rgb, hair_name)
                    a = np.clip(hair_alpha, 0, 1)[..., None]
                    result = np.clip(skinned * (1 - a) + hair_coloured * a, 0, 255)
                    if gender == "male":
                        expected_lower = skinned[330:, :, :]
                        actual_lower = result[330:, :, :]
                        if not np.array_equal(np.rint(expected_lower).astype(np.uint8), np.rint(actual_lower).astype(np.uint8)):
                            raise SystemExit(f"Male body lock violated by hairstyle: {skin_name}/{hair_name}/{style}")
                    out = Image.fromarray(np.rint(result).astype(np.uint8), "RGB")
                    path = legacy.base.OUTPUT / gender / skin_name / hair_name / f"{style}.webp"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    out.save(path, "WEBP", quality=legacy.WEBP_QUALITY, method=legacy.WEBP_METHOD)
                    written += 1
    expected = 125 if requested_gender else 250
    if written != expected:
        raise SystemExit(f"Unexpected creator preset count: {written}, expected {expected}")
    print(f"Built {written} fixed-body creator presets anchored to canonical face")


build_locked_presets()
