from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets' / 'creator_sources' / 'fullbody'
HAIR_DIR = SRC / 'hair'
OUT = ROOT / 'assets' / 'creator' / 'male'
SIZE = (1728, 910)
SKINS = {
    'light': (222, 174, 145),
    'warm': (194, 130, 87),
    'medium': (154, 96, 62),
    'deep': (111, 68, 45),
    'dark': (75, 45, 31),
}
HAIRS = ['black', 'brown', 'blond', 'red', 'purple']
STYLES = ['male_textured', 'male_short', 'male_medium', 'male_undercut', 'male_slick']

HAIR_PLACEMENT = {
    'male_textured': {'width': 1.34, 'bottom': 0.56, 'x': 0.00},
    'male_short': {'width': 1.22, 'bottom': 0.50, 'x': 0.00},
    'male_medium': {'width': 1.48, 'bottom': 0.78, 'x': 0.00},
    'male_undercut': {'width': 1.24, 'bottom': 0.54, 'x': 0.00},
    'male_slick': {'width': 1.34, 'bottom': 0.56, 'x': 0.01},
}


def fit(im, mode):
    if im.size == SIZE:
        return im.convert(mode)
    return ImageOps.fit(im.convert(mode), SIZE, Image.Resampling.LANCZOS)


def load_background():
    return fit(Image.open(SRC / 'background.webp'), 'RGB')


def load_base_scene():
    bg = load_background().convert('RGBA')
    base = fit(Image.open(SRC / 'male_base.png'), 'RGBA')
    alpha = np.asarray(base.getchannel('A'), dtype=np.uint8)
    ys, xs = np.where(alpha > 18)
    if len(xs) < 1000:
        raise SystemExit('male_base.png has no usable full-body alpha')
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if (y1 - y0 + 1) < 600 or y1 < int(SIZE[1] * .82):
        raise SystemExit(f'male_base.png is not full body: bbox={(x0,y0,x1,y1)}')
    bg.alpha_composite(base)
    return bg.convert('RGB'), base


def tint_skin(scene_rgb, mask_img, target):
    rgb = np.asarray(scene_rgb, dtype=np.uint8)
    mask = (np.asarray(fit(mask_img, 'L'), dtype=np.float32) / 255.0).copy()
    mask[int(SIZE[1] * .42):, :] = 0.0
    mask[mask < .06] = 0.0
    src_lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    target_lab = cv2.cvtColor(np.asarray(target, dtype=np.uint8).reshape(1,1,3), cv2.COLOR_RGB2LAB)[0,0].astype(np.float32)
    toned = src_lab.copy()
    toned[...,0] = np.clip(src_lab[...,0] * .88 + target_lab[0] * .12, 0, 255)
    toned[...,1] = np.clip(src_lab[...,1] * .28 + target_lab[1] * .72, 0, 255)
    toned[...,2] = np.clip(src_lab[...,2] * .28 + target_lab[2] * .72, 0, 255)
    toned = cv2.cvtColor(toned.astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
    a = cv2.GaussianBlur(mask, (0,0), .45)[...,None] * .80
    out = np.clip(rgb.astype(np.float32) * (1-a) + toned * a, 0, 255).astype(np.uint8)
    return Image.fromarray(out, 'RGB')


def detect_face_anchor(mask_img, base_img):
    mask = np.asarray(fit(mask_img, 'L'), dtype=np.uint8).copy()
    mask[int(SIZE[1] * .40):, :] = 0
    binary = (mask > 24).astype(np.uint8)
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)

    base_alpha = np.asarray(fit(base_img, 'RGBA').getchannel('A'), dtype=np.uint8)
    ys, xs = np.where(base_alpha > 18)
    body_cx = float((xs.min() + xs.max()) / 2) if len(xs) else SIZE[0] / 2

    candidates = []
    for idx in range(1, count):
        x, y, w, h, area = stats[idx]
        cx, cy = centroids[idx]
        if area < 180 or y > SIZE[1] * .36:
            continue
        centre_penalty = abs(cx - body_cx)
        score = area - centre_penalty * 3.0 - y * 0.15
        candidates.append((score, (int(x), int(y), int(x+w-1), int(y+h-1))))

    if not candidates:
        raise SystemExit('Unable to detect face anchor from male_skin_mask.png')

    _, box = max(candidates, key=lambda item: item[0])
    x0, y0, x1, y1 = box
    if (x1-x0) < 35 or (y1-y0) < 45:
        raise SystemExit(f'Detected face anchor is implausible: {box}')
    print(f'Face anchor detected: {box}')
    return box


def load_hair(style, colour, face_box):
    path = HAIR_DIR / f'{style}_{colour}.png'
    if not path.exists():
        raise SystemExit(f'Missing hair source: {path}')

    raw = fit(Image.open(path), 'RGBA')
    alpha = np.asarray(raw.getchannel('A'), dtype=np.uint8)
    ys, xs = np.where(alpha > 20)
    if len(xs) < 50:
        raise SystemExit(f'Empty hair alpha: {path}')

    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    crop = raw.crop((x0, y0, x1 + 1, y1 + 1))

    fx0, fy0, fx1, fy1 = face_box
    face_w = fx1 - fx0 + 1
    face_h = fy1 - fy0 + 1
    face_cx = (fx0 + fx1) / 2.0

    placement = HAIR_PLACEMENT[style]
    target_w = max(24, int(round(face_w * placement['width'])))
    scale = target_w / max(1, crop.width)
    target_h = max(20, int(round(crop.height * scale)))
    target_h = min(target_h, int(face_h * 1.35))
    target_w = min(target_w, int(face_w * 1.65))
    crop = crop.resize((target_w, target_h), Image.Resampling.LANCZOS)

    cx = face_cx + face_w * placement['x']
    left = int(round(cx - target_w / 2))
    bottom = int(round(fy0 + face_h * placement['bottom']))
    top = bottom - target_h
    left = max(0, min(SIZE[0] - target_w, left))
    top = max(0, min(SIZE[1] - target_h, top))

    layer = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    layer.alpha_composite(crop, (left, top))
    a = np.array(layer.getchannel('A'), dtype=np.uint8, copy=True)
    a[a < 26] = 0
    layer.putalpha(Image.fromarray(a, 'L'))

    ys2, xs2 = np.where(a > 20)
    if len(xs2) < 50:
        raise SystemExit(f'Positioned hair became empty: {path}')
    hx0, hx1, hy0, hy1 = int(xs2.min()), int(xs2.max()), int(ys2.min()), int(ys2.max())
    if hy1 >= int(SIZE[1] * .43):
        raise SystemExit(f'Positioned hair reaches torso: {path} y1={hy1}')
    if abs(((hx0 + hx1) / 2) - face_cx) > face_w * .35:
        raise SystemExit(f'Hair is not centred on face: {path} hair={(hx0,hy0,hx1,hy1)} face={face_box}')
    return layer


def main():
    base_scene, base_rgba = load_base_scene()
    skin_mask = Image.open(SRC / 'male_skin_mask.png')
    face_box = detect_face_anchor(skin_mask, base_rgba)
    written = 0
    for skin_name, skin_rgb in SKINS.items():
        skinned = tint_skin(base_scene, skin_mask, skin_rgb).convert('RGBA')
        for colour in HAIRS:
            for style in STYLES:
                result = skinned.copy()
                result.alpha_composite(load_hair(style, colour, face_box))
                out = result.convert('RGB')
                path = OUT / skin_name / colour / f'{style}.webp'
                path.parent.mkdir(parents=True, exist_ok=True)
                out.save(path, 'WEBP', quality=100, method=6)
                written += 1
    if written != 125:
        raise SystemExit(f'Expected 125 male assets, wrote {written}')
    print('Built 125 male presets with face-anchored, uniformly scaled dedicated hair layers.')


if __name__ == '__main__':
    main()
