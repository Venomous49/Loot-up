from pathlib import Path
import hashlib

import cv2
import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'assets' / 'creator_sources' / 'fullbody'
OUT = ROOT / 'assets' / 'creator' / 'male'
SIZE = (1728, 910)
SKINS = {
    'light': (222, 174, 145),
    'warm': (194, 130, 87),
    'medium': (154, 96, 62),
    'deep': (111, 68, 45),
    'dark': (75, 45, 31),
}
HAIRS = ['black','brown','blond','red','purple']
STYLES = ['male_textured','male_short','male_medium','male_undercut','male_slick']


def fit(im, mode):
    if im.size == SIZE:
        return im.convert(mode)
    return ImageOps.fit(im.convert(mode), SIZE, Image.Resampling.LANCZOS)


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
    return out


def bbox(mask):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def outside_diff_ok(a, b, allowed, mean_limit=.55, p99_limit=5.0):
    d = cv2.absdiff(a, b).astype(np.float32)
    pixels = d[~allowed]
    if pixels.size == 0:
        return True, 0.0, 0.0
    mean = float(pixels.mean())
    p99 = float(np.percentile(pixels, 99))
    return mean <= mean_limit and p99 <= p99_limit, mean, p99


# Locked full-body base and background.
base_rgba = fit(Image.open(SRC / 'male_base.png'), 'RGBA')
base_alpha = np.asarray(base_rgba.getchannel('A'), dtype=np.uint8)
ys, xs = np.where(base_alpha > 18)
if len(xs) < 1000:
    raise SystemExit('Dedicated male fullbody base has no usable alpha')
x0,x1,y0,y1 = int(xs.min()),int(xs.max()),int(ys.min()),int(ys.max())
if y1-y0+1 < 600 or y1 < 750:
    raise SystemExit(f'Dedicated male base is not head-to-feet: {(x0,y0,x1,y1)}')

background = fit(Image.open(SRC / 'background.webp'), 'RGB').convert('RGBA')
background.alpha_composite(base_rgba)
base_scene = np.asarray(background.convert('RGB'), dtype=np.uint8)
skin_mask_img = Image.open(SRC / 'male_skin_mask.png')
skin_mask_u8 = np.asarray(fit(skin_mask_img, 'L'), dtype=np.uint8).copy()
skin_mask_u8[int(SIZE[1] * .42):, :] = 0
skin_allowed = skin_mask_u8 > 12
skin_allowed = cv2.dilate(skin_allowed.astype(np.uint8), np.ones((9,9), np.uint8), iterations=1).astype(bool)

# Detect the head/face component close to the body centre.
face_binary = (skin_mask_u8 > 24).astype(np.uint8)
count, labels, stats, centroids = cv2.connectedComponentsWithStats(face_binary, 8)
body_cx = float((x0 + x1) / 2)
candidates = []
for i in range(1, count):
    sx, sy, sw, sh, area = stats[i]
    cx, cy = centroids[i]
    if area < 80 or sy > int(SIZE[1] * .38):
        continue
    score = area - abs(cx - body_cx) * 2.0 - sy * .05
    candidates.append((score, sx, sy, sx + sw - 1, sy + sh - 1))
if not candidates:
    fb = bbox(face_binary > 0)
    if fb is None:
        raise SystemExit('Cannot detect face/head anchor from male skin mask')
    fx0, fy0, fx1, fy1 = fb
else:
    _, fx0, fy0, fx1, fy1 = max(candidates)
fw, fh = max(1, fx1-fx0+1), max(1, fy1-fy0+1)
fcx = (fx0 + fx1) / 2

# Hair is allowed only in a generous head envelope; never on torso/clothes/background elsewhere.
hx0 = max(0, int(fcx - fw * 1.75))
hx1 = min(SIZE[0]-1, int(fcx + fw * 1.75))
hy0 = max(0, int(fy0 - fh * 1.80))
hy1 = min(int(SIZE[1] * .43), int(fy1 + fh * 1.20))
hair_allowed = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
hair_allowed[hy0:hy1+1, hx0:hx1+1] = True

# Background pixels are everything outside the original character silhouette and permitted hair envelope.
char_dilated = cv2.dilate((base_alpha > 18).astype(np.uint8), np.ones((7,7), np.uint8), iterations=1).astype(bool)
background_region = ~(char_dilated | hair_allowed)

files = list(OUT.rglob('*.webp'))
if len(files) != 125:
    raise SystemExit(f'Expected 125 male assets, got {len(files)}')

images = {}
for skin in SKINS:
    for hair in HAIRS:
        for style in STYLES:
            p = OUT / skin / hair / f'{style}.webp'
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if im is None or im.shape[:2] != (910,1728):
                raise SystemExit(f'Bad asset: {p}')
            images[(skin,hair,style)] = im

# 1) All 25 hairstyle/colour presets must genuinely differ for every skin.
for skin in SKINS:
    digests = {
        hashlib.sha256((OUT / skin / hair / f'{style}.webp').read_bytes()).hexdigest()
        for hair in HAIRS for style in STYLES
    }
    if len(digests) != 25:
        raise SystemExit(f'Expected 25 distinct style/color assets for {skin}, got {len(digests)}')

# 2) Hair changes may alter only the head envelope. Clothes, body and background remain locked.
for skin in SKINS:
    ref = images[(skin,'brown','male_undercut')]
    for hair in HAIRS:
        for style in STYLES:
            im = images[(skin,hair,style)]
            ok, mean, p99 = outside_diff_ok(ref, im, hair_allowed, .60, 5.5)
            if not ok:
                raise SystemExit(f'Hair changed body/clothes/background: {skin}/{hair}/{style} mean={mean:.3f} p99={p99:.2f}')

# 3) Skin changes may alter only the reviewed skin mask. No clothing tint, no background tint, no stray skin spots.
for hair in HAIRS:
    for style in STYLES:
        ref = images[('medium',hair,style)]
        for skin in SKINS:
            im = images[(skin,hair,style)]
            ok, mean, p99 = outside_diff_ok(ref, im, skin_allowed, .60, 5.5)
            if not ok:
                raise SystemExit(f'Skin tone leaked outside skin mask: {skin}/{hair}/{style} mean={mean:.3f} p99={p99:.2f}')

# 4) Background must be invariant across every one of the 125 exports.
ref_bg = images[('medium','brown','male_undercut')]
for key, im in images.items():
    d = cv2.absdiff(ref_bg, im).astype(np.float32)[background_region]
    mean = float(d.mean()) if d.size else 0.0
    p99 = float(np.percentile(d,99)) if d.size else 0.0
    if mean > .45 or p99 > 4.5:
        raise SystemExit(f'Background changed for {key}: mean={mean:.3f} p99={p99:.2f}')

# 5) Verify each generated hairstyle is actually located on the detected head, not floating or oversized.
# Rebuild the no-hair skinned base and inspect only meaningful deltas (compression noise ignored).
for skin, skin_rgb in SKINS.items():
    no_hair_rgb = tint_skin(base_scene, skin_mask_img, skin_rgb)
    no_hair_bgr = cv2.cvtColor(no_hair_rgb, cv2.COLOR_RGB2BGR)
    for hair in HAIRS:
        for style in STYLES:
            im = images[(skin,hair,style)]
            delta = cv2.absdiff(no_hair_bgr, im)
            significant = (delta.max(axis=2) > 16).astype(np.uint8)
            significant = cv2.morphologyEx(significant, cv2.MORPH_OPEN, np.ones((3,3),np.uint8))
            hb = bbox(significant > 0)
            if hb is None:
                raise SystemExit(f'No visible hairstyle detected: {skin}/{hair}/{style}')
            ax0, ay0, ax1, ay1 = hb
            aw, ah = ax1-ax0+1, ay1-ay0+1
            acx = (ax0+ax1)/2
            # Hair must overlap the face horizontally and remain in a realistic scale range.
            overlap_x = max(0, min(ax1,fx1)-max(ax0,fx0)+1)
            if overlap_x < max(4, int(fw * .30)):
                raise SystemExit(f'Hairstyle does not overlap face: {skin}/{hair}/{style} bbox={hb} face={(fx0,fy0,fx1,fy1)}')
            if abs(acx-fcx) > fw * 1.10:
                raise SystemExit(f'Hairstyle horizontally misaligned: {skin}/{hair}/{style} bbox={hb}')
            if aw < fw * .55 or aw > fw * 3.6 or ah < fh * .25 or ah > fh * 3.4:
                raise SystemExit(f'Hairstyle scale invalid: {skin}/{hair}/{style} bbox={hb} face={(fx0,fy0,fx1,fy1)}')
            outside = significant.astype(bool) & ~hair_allowed
            if int(outside.sum()) > max(40, int(significant.sum() * .015)):
                raise SystemExit(f'Hairstyle spills outside head envelope: {skin}/{hair}/{style} pixels={int(outside.sum())}')

print('STRICT PASS: 125 male creator presets are full-body, hair is head-aligned, skin is mask-confined, clothing/body are locked, and background is invariant.')
