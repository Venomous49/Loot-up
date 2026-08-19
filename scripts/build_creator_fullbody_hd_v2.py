from pathlib import Path
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
    """Extract the whole person from the native master without using legacy reviewed masks.

    The previous reviewed masks were the source of the beige/black 'melted' character bug:
    they contained holes/background fragments that were then pasted as if they were the body.
    This mask is rebuilt from the actual pixels using GrabCut and keeps only the largest person.
    """
    rgb = np.asarray(image, dtype=np.uint8)
    h, w = rgb.shape[:2]
    preview_w = min(700, w)
    scale = preview_w / w
    preview = cv2.resize(rgb, (preview_w, max(2, round(h * scale))), interpolation=cv2.INTER_AREA)
    ph, pw = preview.shape[:2]

    gc = np.zeros((ph, pw), np.uint8)
    if gender == "male":
        rect = (int(.24 * pw), int(.01 * ph), int(.52 * pw), int(.98 * ph))
    else:
        rect = (int(.20 * pw), int(.01 * ph), int(.60 * pw), int(.98 * ph))
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
    if not len(xs):
        raise SystemExit(f"Empty canonical {gender} mask")
    bbox_h = ys.max() - ys.min() + 1
    if bbox_h < h * .48:
        raise SystemExit(f"Canonical {gender} extraction is not full-body enough ({bbox_h}/{h})")
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
    layer = cv2.GaussianBlur(layer, (0, 0), 1.15)
    return Image.fromarray(layer, "L")


def robust_canonical_body(gender):
    path, _ = legacy.CANONICAL[gender]
    scene = native_scene(path)
    person_alpha = robust_person_mask(scene, gender)
    bbox = person_alpha.getbbox()
    if not bbox:
        raise SystemExit(f"No canonical {gender} body bbox")

    skin = native_skin_mask(scene, person_alpha)
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
    if x < 0 or x + target_w > legacy.CANVAS_SIZE[0] or y < 0:
        raise SystemExit(f"Canonical {gender} placement clips canvas")

    body = legacy.BACKGROUND.copy()
    body.paste(cutout, (x, y), cutout_alpha)

    skin_layer = Image.new("L", legacy.CANVAS_SIZE, 0)
    skin_layer.paste(skin_crop, (x, y))
    skin_layer = skin_layer.filter(ImageFilter.GaussianBlur(.8))
    return body, np.asarray(skin_layer, dtype=np.float32) / 255.0


# Critical hotfix: keep the existing hairstyle/colour pipeline, but replace only the
# body extraction stage that generated the grotesque hollow/patchy avatars.
legacy.canonical_body = robust_canonical_body
legacy.build()
